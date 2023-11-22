import unittest
from test.helper import single_guide_stdin_cmd, dual_guide_stdin_cmd
import pandas as pd
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    datefmt='%Y-%m-%d %H:%M:%S',
)


class TestCount(unittest.TestCase):
    """
    Functional test cases to execute and validate results.
    """

    def test_main_single_guide(self):
        """
        Test case for single guide counting.
        """
        output_file = "test-output/test_single.out"
        ret = single_guide_stdin_cmd(
            "count.py",
            "test-data/plasmid.fq.gz",
            "test-data/cleanr.tsv.gz",
            output_file,
        )
        self.assertEqual(0, ret, "Command line invocation failed")
        df = pd.read_csv(output_file, sep='\t', names=["Code", "Symbol", "Count"])
        logging.debug(f"Row count of output file: {len(df)}")

        self.assertTrue(len(df) > 0, "Row count of the output file cannot be zero")
        self.assertEqual(110588, len(df), "Unexpected number of output file rows")
        total_matches = df['Count'].sum()
        logging.debug(f"Total matches : {total_matches}")
        self.assertEqual(230177, total_matches, "Total matches not as expected.")

    def test_main_dual_guide(self):
        """
        Test case for dual guide counting.
        """
        output_file = "test-output/test_dual.out"
        ret = dual_guide_stdin_cmd(
            "count.py",
            "test-data/dual_guide_r1.fq.gz",
            "test-data/dual_guide_r2.fq.gz",
            "test-data/cleanr_fake_dual_guide.tsv.gz",
            output_file,
            dual_guide=True,
        )

        self.assertEqual(0, ret, "Command line invocation failed")
        df = pd.read_csv(output_file, sep='\t', names=["Code", "Symbol", "Count"])
        logging.debug(f"Row count of output file: {len(df)}")
        self.assertTrue(len(df) > 0, "Row count of the output file cannot be zero")
        self.assertEqual(2, len(df), "Unexpected number of output file rows")
        total_matches = df['Count'].sum()
        logging.debug(f"Total matches : {total_matches}")
        self.assertEqual(3, total_matches, "Total matches not as expected")


if __name__ == "__main__":
    unittest.main()
