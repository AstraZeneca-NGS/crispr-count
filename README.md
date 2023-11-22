# CRISPR guide counter for single and dual guide libraries

This program takes as input a [CRISPR library file](#library-format) and nucleotide sequences either from a file or stdin. It counts the exact occurrences of guides from the library in the input sequences. Reverse complements of guides are by default counted as hits; this behaviour can be switched off. Libraries with reverse complement guides are discouraged.

## Library format

For single guide libraries the input library file must have tab delimited columns for `SEQ` (guide sequence), `CODE` (guide name) and `GENE` (gene name). For dual guide libraries there must also be a `SEQ2` column corresponding to the second guide in the construct (R2 file), and the ```--dual_guide``` option should be used. See [Library file formats](#library-file-formats) for more detail.

## Usage

### Container

Build the container and run `count.py` (look at the targets and examples in the [Makefile](Makefile)).

### Local

You must have a [configured and activated python environment](runbooks/create-python-env.md).

## Single guide library example

```shellsession
gzip --decompress --to-stdout test-data/plasmid.fq.gz | awk "NR%4==2" | \
    ./count.py --lib <(gzip --decompress --to-stdout test-data/cleanr.tsv.gz) --input - --out test-output/python.count
```

This shell command:

* uncompresses a gzipped [FASTQ](https://en.wikipedia.org/wiki/FASTQ_format) file `plasmid.fq.gz`
* uses `awk`(1) to take the second line from each group of four lines (ie just the sequence)
* feeds the sequence lines into `count.py` on stdin (`--input -`)
* outputs a count into `test-output/python.count`; the expected output should begin like this:

```shellsession
$ head -4 test-output/python.count
C15orf48_v3_5-3 C15orf48        0
CENPH_v3_5-5    CENPH   1
ETV7_v3_15-15   ETV7    1
MRGPRX4_v3_6-4  MRGPRX4 0
```

You will also see some progress and summary information on stderr:

``` shellsession
2021-11-16 10:33:09 INFO     count.py Input library file: -
2021-11-16 10:33:09 INFO     count.py Dual guide library: False
2021-11-16 10:33:09 INFO     count.py Count reverse complements: True
2021-11-16 10:33:09 INFO     count.py Processes: 1
2021-11-16 10:33:20 INFO     reads  unique matches  multi matches  mismatching pairs  250000  230039  69  0
```

## Dual guide library example

Here we use Unix ```paste``` to bind the sequences as tab delimited columns and feed into the counting script:

```shellsession
$ paste <(gzip --decompress --to-stdout test-data/dual_guide_r1.fq.gz | awk "NR%4==2" ) \
      <(gzip --decompress --to-stdout test-data/dual_guide_r2.fq.gz | awk "NR%4==2") | \
      python3 count.py --dual_guide --lib <(gzip --decompress --to-stdout test-data/cleanr_fake_dual_guide.tsv.gz) --input - --out test-output/dual.count
2021-11-02 17:08:18 INFO     count.py Input library file: -
2021-11-02 17:08:18 INFO     count.py Dual guide library: True
2021-11-02 17:08:18 INFO     count.py Count reverse complements: True
2021-11-02 17:08:18 INFO     count.py Processes: 1
2021-11-02 17:08:18 INFO     reads      unique matches  multi matches   mismatching pairs
6       3       0       0
```

The expected output is:

```shellsession
$ cat test-output/dual.count
 C15orf48_v3_5-3 C15orf48        1
 CENPH_v3_5-5    CENPH   2
```

```shellsession
$ paste <(gzip -dc test-data/test-dual-guide-count/test-dual-guide-sample--SLX-20701.i714_i511.000000000-JVMBF.s_1.r_1.fq.gz | awk "NR%4==2" ) \
      <(gzip -dc test-data/test-dual-guide-count/test-dual-guide-sample--SLX-20701.i714_i511.000000000-JVMBF.s_1.r_2.fq.gz | awk "NR%4==2") | \
      python3 count.py --dual_guide --lib test-data/test-dual-guide-count/test-dual-guide-annot-library--cleanr.tsv --input - --out test-output/dual.counts
2021-11-02 17:08:44 INFO     count.py Input library file: -
2021-11-02 17:08:44 INFO     count.py Dual guide library: True
2021-11-02 17:08:44 INFO     count.py Count reverse complements: True
2021-11-02 17:08:44 INFO     count.py Processes: 1
2021-11-02 17:08:44 INFO     reads      unique matches  multi matches   mismatching pairs
165     89      0       41
```

The expected output is:

```shellsession
$ cat test-output/dual.counts
Vienna_A1BG_1-Vienna_A1BG_4     A1BG    62
Vienna_A1CF_1-Vienna_A1CF_4     A1CF    27
Vienna_A2M_1-Vienna_A2M_4       A2M     0
Vienna_A2ML1_1-Vienna_A2ML1_4   A2ML1   0
```

## Command line parameters

For parallelisation see the `processes` option. For not counting reverse complement matches use the `--no_rev_comp` option. ℹ️ Check the `--help` option of the script for more information.

## Developing

This document assumes you're developing under Linux, macOS, or WSL2 (Ubuntu under Windows). To do everything, you'll need `make`(1) and `awk`(1), as well as Python and the other tools mentioned below—eg Docker, Hadolint.

### Environment setup

In the dev and production containers we install the python dependencies using pip.
When developing `count.py` on your laptop it makes sense to have a local [environment](runbooks/create-python-env.md) for testing.

### Building the Docker container

The container encapsulates the Python program in a Linux container with all the dependencies. It is based on a [Python](https://hub.docker.com/_/python) image, see the `Dockerfile` for more details. To build the container:

* you will need [Docker BuildKit](https://docs.docker.com/develop/develop-images/build_enhancements/), and Docker should be running
* [`hadolint`](https://github.com/hadolint/hadolint) must be installed
* From the root directory of the repo run `make -C python build-candidate` or `make -C python release`

ℹ️ The target `release` will build the image, run the tests, and if they pass tag it `count_guides_dual:latest`.

The container by default is configured to be built from the root directory of the repo, but you can also modify the path using the option `--build-arg START_FROM='[PATH]'` so the `COPY` commands in the Dockerfile will use the correct path to the files. Look at the [examples](Makefile) in the Makefile.

There are two targets in the Dockerfile: `build` and `dev`, been the second the default target.
You can specify the target in the `docker build` using the option `--target [TARGET]`. Look at the [examples](Makefile) in the Makefile.

### Run tests locally

You can run the tests independently from building the Docker container. Don't forget to [configure and activate](runbooks/create-python-env.md) your python environment. The target `make -C python python-test-locally` should run the functional and local tests.

#### Functional tests

These tests live in `test/`, and were originally supplied by AstraZeneca; they will leave output in `test-output/`. To clean that up, `make -C python clean`. To run the tests:

* From the `python/` directory run:

```shellsession
python3 -m unittest
```

#### End-to-end local tests

These live in `tests/`, and use the [pytest workflow](https://pytest-workflow.readthedocs.io/en/stable/#test-options). Run them with `pytest`.

ℹ️ If you want to keep the test tree including the output data in a temporary directory, eg to check the count files, run `pytest --keep-workflow-wd --basetemp <temporary directory>`.

The `--keep-workflow-wd-on-fail` flag used to run these tests from the `Makefile` will leave a copy of the scripts, test data and the logs behind in a temporary directory only if the tests fail. ⚠️ This can use a significant amount of disk space over time, so don't forget to clean them up every now and then—check the test logs for the storage location.

#### End-to-end Docker tests

These run using the `count.py` baked into the `count_guides_dual:dev` container; make sure that you have that [up to date](#building-the-docker-container) first with `make -C python build-dev`, and then `make -C python test-single-guide`, `make -C python test-dual-guide`, and/or `make -C python test-python-expected-output`.

#### Troubleshooting

* On WSL2, if you see `The command 'docker' could not be found in this WSL 2 distro.` ensure that you are running Docker Desktop. If you weren't, you might need to start another terminal session after you have started it.
* If you get `failed to solve with frontend dockerfile.v0: failed to solve with frontend gateway.v0: failed to authorize: rpc error: code = Unknown desc = failed to fetch oauth token: unexpected status: 400 Bad Request`, try clearing Docker Desktop's cache:
  * Docker-desktop / 🐞 Troubleshoot / Clean/Purge data

## Library file formats

All of these files are tab separated. 

### Library formats

These are the library file formats expected by `count.py` in this repository.

#### Single-guide

```text
CODE         GENES SEQ                  EXONE CHRM STRAND STARTpos  ENDpos
Croatan.192  ALG1  AACCAGCAGACAGCAATGCT .     16   -      5075403   5075425
brunello.87  ALPI  CCGTTCGCAGACATACAATG .     2    +      232456889 232456911
HGLibB_02636 ARCN1 ATACCGGGAGAATGTTAACT .     11   +      118583271 118583293
[…]
```

#### Dual-guide

Dual guide library files must also have a `SEQ2` column (in an intermediate version this was called `CODE2`; if you see that in a library it is an old format and should not be used). This is sufficient:

```text
CODE              GENES  SEQ                  SEQ2
Brunello_AAMP_1_3 AAMP   AAGATGACAAAGCCTTCGTA TGAGTGGCCTCTTGAAAGTG
Brunello_AAMP_2_4 AAMP   TGGATGTGGAAAGTCCCGAA AGGTGACCTCGCTATCGTCG
Brunello_AAMP_3_1 AAMP   TGAGTGGCCTCTTGAAAGTG AAGATGACAAAGCCTTCGTA
Brunello_AAMP_4_2 AAMP   AGGTGACCTCGCTATCGTCG TGGATGTGGAAAGTCCCGAA
[…]
```

…but this is also valid, and more complete:

```text
CODE GENES SEQ SEQ2 EXONE CHRM STRAND STARTpos ENDpos CHRM2 STRAND2 STARTpos2 ENDpos2
```

### Converting library formats

To convert from the old style to the new style, see `library_reorder.py`; this reorders and renames the columns appropriately. Two columns change name, and the first three columns change position:

| old     | new    | description       |
|:--------|:-------|:------------------|
| `CODE`  | `SEQ`  | guide nucleotides |
| `GUIDE` | `CODE` | guide names       |

Column order before:

```text
CODE                 GUIDE            GENES                EXONE  CHRM  STRAND  STARTpos  ENDpos
AAAAAAAAATCCAGAACCT  C15orf48_v3_5-3  C15orf48             .      15    +       45432081  45432102
AAAAAAGCTTGCATTAGAC  CENPH_v3_5-5     CENPH                .      5     +       69195771  69195792
[…]
```

After:

```text
CODE                 GENES            SEQ                  EXONE  CHRM  STRAND  STARTpos  ENDpos
C15orf48_v3_5-3      C15orf48         AAAAAAAAATCCAGAACCT  .      15    +       45432081  45432102
CENPH_v3_5-5         CENPH            AAAAAAGCTTGCATTAGAC  .      5     +       69195771  69195792
[…]
```
