import argparse
import subprocess
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S')


def get_args(input_file, lib_file, output_file, rev_com=False, dual_guide=False):
    """
    Function to mimic command line arguments for tests.
    :param input_file: FQ file path
    :param lib_file: library file path
    :param output_file: output file path
    :param rev_com: Enable reverse complement search or not(True/False)
    :param dual_guide: Enable dual guid counting or not(True/False)
    :return: args parser object
    """
    parser = argparse.ArgumentParser(description='Count instances of CRISPR guides in input nucleotide sequences.')
    parser.add_argument('--no_rev_comp', help='Do not count reverse complements additionally', action="store_false")
    parser.add_argument('--dual_guide', help='Library contains dual guides', action="store_true", default=dual_guide)
    parser.add_argument('--lib', default=lib_file)
    parser.add_argument('--dual_guide_seq_sep', default="\t")
    parser.add_argument('--out', help='Output text file name.', default=output_file)
    parser.add_argument('--input', default=input_file)
    return parser.parse_args()


def single_guide_file_cmd(script_path, input_file, lib_file, output_file, rev_com=False, dual_guide=False):
    """
    Execute single guide command(on command-line) file path as input.
    :param script_path: path of the python script file
    :param input_file: FQ file path
    :param lib_file: library file path
    :param output_file: output file path
    :param rev_com: Enable reverse complement search or not(True/False)
    :param dual_guide: Enable dual guid counting or not(True/False)
    :return: command line return value
    """
    # E.g. python3 count.py --lib ../fastq/cleanr-guide.tsv --out output14.count
    # --input /projects/fg/crispr_screening/datasets/SLX-17741/SLX-17741.H7C7MBBXY.s_4.r_1.lostreads.fq.gz
    cmd = f'python3 {script_path} --lib {lib_file}  --out {output_file} --input {input_file}'
    logging.debug(f"Command to run: {cmd} ")
    return subprocess.call(cmd, shell=True)


def single_guide_stdin_cmd(script_path, input_file, lib_file, output_file, rev_com=False, dual_guide=False):
    """
    Execute single guide command(on command-line) with input comes in stdin.
    :param script_path: path of the python script file
    :param input_file: FQ file path
    :param lib_file: library file path
    :param output_file: output file path
    :param rev_com: Enable reverse complement search or not(True/False)
    :param dual_guide: Enable dual guid counting or not(True/False)
    :return: command line return value
    """
    # E.g. gzip -dc /projects/fg/crispr_screening/datasets/SLX-17741/SLX-17741.H7C7MBBXY.s_4.r_1.lostreads.fq.gz | awk "NR%4==2"
    # | python3 count.py --lib ../fastq/cleanr-guide.tsv --out output14.count --input -
    cmd = f'gzip -dc {input_file} | awk "NR%4==2" | python3 {script_path} --lib {lib_file}  --out {output_file} --input -'
    logging.debug(f"Command to run: {cmd} ")
    return subprocess.call(cmd, shell=True)


def dual_guide_stdin_cmd(script_path, input_file1, input_file2, lib_file, output_file, rev_com=False, dual_guide=False):
    """
    Execute dual guide command(on command-line) with input comes in stdin.
    :param script_path: path of the python script file
    :param input_file1: source FQ file 1
    :param input_file2: source FQ file 2
    :param lib_file: library file path
    :param output_file: output file path
    :param rev_com: Enable reverse complement search or not(True/False)
    :param dual_guide: Enable dual guid counting or not(True/False)
    :return: command line return value
    """
    # E.g. paste <(gzip -dc test/dual_guide_r1.fq.gz | awk "NR%4==2" ) <(gzip -dc test/dual_guide_r2.fq.gz | awk "NR%4==2") |
    # python3 count.py --dual_guide --lib test/cleanr_fake_dual_guide.tsv.gz --input - --out dual.count
    dual_guide_str = "--dual_guide" if dual_guide else ""
    cmd = f"paste <(gzip -dc {input_file1} | awk \"NR%4==2\") <(gzip -dc {input_file2} | awk \"NR%4==2\") | " \
        f"python3 {script_path} {dual_guide_str} --lib {lib_file} --out {output_file} --input -"
    print(f"Command to run: {cmd} ")
    return subprocess.call(cmd, shell=True, executable="/bin/bash")


def dual_guide_file_cmd(script_path, input_file1, input_file2, lib_file, output_file, rev_com=False, dual_guide=False):
    """
    Execute dual guide command(on command-line) with input comes in stdin.
    :param script_path: path of the python script file
    :param input_file1: source FQ file 1
    :param input_file2: source FQ file 2
    :param lib_file: library file path
    :param output_file: output file path
    :param rev_com: Enable reverse complement search or not(True/False)
    :param dual_guide: Enable dual guid counting or not(True/False)
    :return: command line return value
    """
    # E.g. paste <(gzip -dc test/dual_guide_r1.fq.gz | awk "NR%4==2" ) <(gzip -dc test/dual_guide_r2.fq.gz | awk "NR%4==2") |
    # python3 count.py --dual_guide --lib test/cleanr_fake_dual_guide.tsv.gz --input - --out dual.count
    dual_guide_str = "--dual_guide" if dual_guide else ""
    cmd = f"paste <(gzip -dc {input_file1} | awk \"NR%4==2\") <(gzip -dc {input_file2} | awk \"NR%4==2\") | " \
        f"python3 {script_path} {dual_guide_str} --lib {lib_file} --out {output_file} --input -"
    print(f"Command to run: {cmd} ")
    return subprocess.call(cmd, shell=True, executable="/bin/bash")
