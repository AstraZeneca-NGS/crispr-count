#!/usr/bin/env python
"""Take an input library TSV file in the "new" format, and convert it to the "old" format. Requires all
eight column headers, so will not work with the old-old format, where the "CODE" header is omitted.

This is effectively a prequel to documenting the library formats; see the README.md for further
information.
"""
import click
import csv


@click.command()
@click.option(
    "--input",
    required=True,
    help="the input file",
)
@click.option(
    "--output",
    required=True,
    help="the output file",
)
def main(input, output):
    with open(input, "r") as infile, open(output, "w") as outfile:

        writer = csv.DictWriter(
            outfile,
            fieldnames=[
                "CODE",
                "GUIDE",
                "GENES",
                "EXONE",
                "CHRM",
                "STRAND",
                "STARTpos",
                "ENDpos",
            ],
            delimiter="\t",
        )

        writer.writeheader()
        try:
            for row in csv.DictReader(infile, delimiter="\t"):
                writer.writerow(
                    {
                        "GUIDE": row["CODE"],
                        "GENES": row["GENES"],
                        "CODE": row["SEQ"],
                        "EXONE": row["EXONE"],
                        "CHRM": row["CHRM"],
                        "STRAND": row["STRAND"],
                        "STARTpos": row["STARTpos"],
                        "ENDpos": row["ENDpos"],
                    }
                )
        except KeyError as e:
            print(f'Can\'t find this column in input "{input}": {e}')


if __name__ == "__main__":
    main()
