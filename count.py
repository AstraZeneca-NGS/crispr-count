#!/usr/bin/env python
"""
Single and dual CRISPR guide counting the program.

Single guide counting : counts exact matches of guides located in an input fastq file.

Dual guide counting : counts exact matches of two guides located in the same row position in two input fastq files.
"""
import pandas as pd
import numpy as np
import ahocorasick, fileinput, argparse, logging
from operator import itemgetter
import concurrent.futures
import platform
import multiprocessing

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

version = '1.0.0'
auto = ahocorasick.Automaton()
auto2 = ahocorasick.Automaton()
temp_output = None
multi_matches = 0
unique_matches = 0
mismatching_pairs = 0


def process_result(future):
    """
    This is a callback function that processes the results coming from completion of forked processors.
    :param future: future object(with results) from the forked process
    """
    global temp_output, multi_matches, unique_matches, mismatching_pairs
    temp_output += future.result()["output"]
    multi_matches += future.result()["multi_matches"]
    unique_matches += future.result()["unique_matches"]
    mismatching_pairs += future.result()["mismatching_pairs"]


def revcomp(seq):
    """
    Generates the reverse complement of the genomic sequence.
    :param seq: genomic sequence
    :return: reverse complement of the given genomic sequence
    """
    return seq.translate(str.maketrans('ACGTacgtRYMKrymkVBHDvbhd', 'TGCAtgcaYRKMyrkmBVDHbvdh'))[::-1]


def main(args):
    """
    For a given CRISPR library use Aho-Corasick to count instances in input
    sequencing reads. Each line of input is assumed to be a nucleotide sequence
    so only every 4th line of fastq.
    """
    # macOS falls over with Python > 3.8 with the now default spawn context
    # https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
    # so we force fork, see https://stackoverflow.com/a/65221779. This is
    # already the default on Linux.
    if platform.system() == 'Darwin':
       multiprocessing.set_start_method('fork')

    # library tsv file (to be added as an option)
    library = pd.read_csv(args.lib, sep="\t")
    count_revcomp = not args.no_rev_comp
    output_file = args.out
    input_file = args.input
    is_dual_guide = args.dual_guide
    processes = int(args.processes)
    block_size = int(args.block_size)
    if count_revcomp:  # help with creating a dictionary by
        library["SEQrev"] = library["SEQ"].apply(revcomp)
        if is_dual_guide:
            library["SEQ2rev"] = library["SEQ2"].apply(revcomp)
    dual_guide_seq_sep = args.dual_guide_seq_sep
    logging.info("count.py Input library file: " + input_file)
    logging.info("count.py Dual guide library: " + str(is_dual_guide))
    logging.info("count.py Count reverse complements: " + str(count_revcomp))
    logging.info("count.py Processes: " + str(processes))
    # resulting dataframe
    outputdf = library[["CODE", "GENES"]]
    # temporary holder for counts (numpy, fast)
    global temp_output
    temp_output = np.zeros(outputdf.shape[0], dtype=int)
    # create automaton for first guides
    loop_through = ["SEQ"]
    if count_revcomp:
        loop_through += ["SEQrev"]
    temp_dict = {}
    for col_head in loop_through:
        for substr, index, guide in zip(library[col_head], outputdf.index, library["CODE"]):
            # add guide sequence to dictionary/tree
            if substr not in temp_dict:
                temp_dict[substr] = {index}
            else:
                temp_dict[substr].add(index)
    # put unique keys into dict
    for my_key in temp_dict:
        auto.add_word(my_key, temp_dict[my_key])
    auto.make_automaton()

    # dual guide library?
    if is_dual_guide:
        temp_dict2 = {}
        loop_through = ["SEQ2"]
        if count_revcomp:
            loop_through += ["SEQ2rev"]
        for col_head in loop_through:
            for substr, index, guide in zip(library[col_head], outputdf.index, library["CODE"]):
                if substr not in temp_dict2:
                    temp_dict2[substr] = {index}
                else:
                    temp_dict2[substr].add(index)
        for my_key in temp_dict2:
            auto2.add_word(my_key, temp_dict2[my_key])
        auto2.make_automaton()
    # Find library sgRNAs in input nucleotide sequences
    counter = 0

    # a temporary holder for sequence reads with each bucket holding a certain number of reads (block_size)
    input_lines_collection = [[] for _ in range(processes)]
    for line in fileinput.input(input_file):  # loop through input sequencing reads
        futures = []
        counter += 1
        # assign reads to buckets
        input_lines_collection[(counter - 1) % processes].append(line)
        if counter % (processes * block_size) > 0:
            continue
        if counter % 1000000 == 0:
            logging.info('count.py Processed reads: ' + str(counter))
        # submit buckets to parallel processing
        with concurrent.futures.ProcessPoolExecutor(max_workers=processes) as executor:
            for input_lines in input_lines_collection:
                futures.append(executor.submit(exec_fragment_search, data_lines=input_lines,
                                               num_guides=outputdf.shape[0], is_dual_guide=is_dual_guide,
                                               dual_guide_seq_sep=dual_guide_seq_sep))
        for future in futures:
            future.add_done_callback(process_result)

        # wait for processing to finish until reading in more sequence reads
        concurrent.futures.wait(futures)

        input_lines_collection = [[] for _ in range(processes)]

    # flush remaining table
    with concurrent.futures.ProcessPoolExecutor(max_workers=processes) as executor:
        futures = []
        for input_lines in input_lines_collection:
            if len(input_lines) > 0:
                futures.append(executor.submit(exec_fragment_search, data_lines=input_lines,
                                               num_guides=outputdf.shape[0], is_dual_guide=is_dual_guide,
                                               dual_guide_seq_sep=dual_guide_seq_sep))
        for future in futures:
            future.add_done_callback(process_result)
    executor.shutdown(wait=True)
    # create output struct from numpy array and guide and gene names
    outputdf.insert(2, "count", pd.Series(temp_output))
    outputdf.to_csv(output_file, sep="\t", header=False, index=False)
    logging.info("reads\tunique matches\tmulti matches\tmismatching pairs\n" + str(counter)
                 + "\t" + str(unique_matches) + "\t" + str(multi_matches) + "\t" + str(mismatching_pairs))


def exec_fragment_search(**input):
    lines = input["data_lines"]
    is_dual_guide = input["is_dual_guide"]
    dual_guide_seq_sep = input["dual_guide_seq_sep"]
    num_guides = input["num_guides"]
    multi_matches = 0
    unique_matches = 0
    mismatching_pairs = 0
    output = np.zeros(num_guides, dtype=int)
    for line in lines:
        if is_dual_guide:
            # input data is expected to be two nucleotide sequences separated by a symbol (default: tab)
            linesplit = line.strip().split(dual_guide_seq_sep)

            # potentially faster way relying a bit on C backend
            matches1 = list(map(itemgetter(1),
                                [*auto.iter(linesplit[0])]))  # use itemgetter to ignore first arg from iterator
            len1 = len(matches1)
            if len1 == 0:
                continue
            matches2 = list(map(itemgetter(1), [*auto2.iter(linesplit[1])]))
            len2 = len(matches2)
            if len2 == 0:
                continue
            # this block takes the lion's share of compute time and if optimised would make a big difference
            if len1 == 1 and len2 == 1:  # both are lists with just one set each
                idxs = list(matches1[0] & matches2[0])
            elif len1 == 1:  # matches1 is a list with one set in it
                idxs = list(matches1[0] & set.union(*matches2))
            elif len2 == 1:  # matches2 is a list with one set in it
                idxs = list(matches2[0] & set.union(*matches1))
            else:  # both lists have multiple sets in them
                idxs = list(set.union(*matches1) & set.union(*matches2))
            # end ^^^^^

            if len(idxs) == 1:
                output[idxs[0]] += 1
                unique_matches += 1
            elif len(idxs) > 1:
                multi_matches += 1
                output[idxs] += 1
                # for loop may be actually faster for small idxs sets
                # for idx in idxs:
                #    output[ idx ] += 1
            else:
                mismatching_pairs += 1
                continue
        else:  # not dual guide
            idxs = [*(y for _, x in auto.iter(line.strip()) for y in x)]
            if len(idxs) == 1:
                output[idxs[0]] += 1
                unique_matches += 1
            elif len(idxs) > 1:
                multi_matches += 1
                output[idxs] += 1
    return {"output": output, "multi_matches": multi_matches,
            "unique_matches": unique_matches, "mismatching_pairs": mismatching_pairs}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Count instances of CRISPR guides in input nucleotide sequences.', prog='count.py')
    # Library
    parser.add_argument('--lib', help='Filename of an input library.', required=True)
    parser.add_argument('--dual_guide', help='Library contains dual guides.', action="store_true")
    # Sequences
    parser.add_argument('--dual_guide_seq_sep', help='Delimiter for sequencing read 1 and 2 when using dual guide libraries [default: tab].', default="\t")
    parser.add_argument('--input', help='Input sequence file name or - for stdin with one nucleotide sequence per line. For dual guides the sequences must be separated with dual_guide_seq_sep.', required=True)
    # Processing
    parser.add_argument('--processes', help='Number of processes to use [default: 1].', default=1)
    parser.add_argument('--block_size', help='Block size for processing given in number of sequencing'
                                             ' reads [default: 25000].', default=25000)
    parser.add_argument('--no_rev_comp', help='Do not count reverse complements additionally.', action="store_true")
    # Output
    parser.add_argument('--out', help='Output text file name. - does not mean stdout.', required=True)

    parser.add_argument('--version', help='Output program name and version number.', action='version', version=f'%(prog)s {version}')
    args = parser.parse_args()
    main(args)
