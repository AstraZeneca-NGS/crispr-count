#!/usr/bin/env python
import argparse
import sys
import pandas as pd


def revcomp(seq):
    """
    Generates the reverse complement of the genomic sequence.
    :param seq: genomic sequence
    :return: reverse complement of the given genomic sequence
    """
    return seq.translate(str.maketrans('ACGTacgtRYMKrymkVBHDvbhd', 'TGCAtgcaYRKMyrkmBVDHbvdh'))[::-1]


def main(args):
    library = pd.read_csv(args.input, sep="\t")
    for colname in args.column_names.split(","):
        library[colname.strip()] = library[colname.strip()].apply(revcomp)
    library.to_csv(sys.stdout, sep="\t")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Reverse complement a column in a library file.')
    parser.add_argument('--input', help='Filename for a tab delimited library file.', required=True)

    parser.add_argument('--column_names', help='Comma delimited list of column names to reverse complement.', required=True)
    args = parser.parse_args()
    main(args)
