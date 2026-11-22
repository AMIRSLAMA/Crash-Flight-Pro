import tempfile
import unittest
from pathlib import Path
from analysis_engine import summary, validate, walk_forward, read_csv
from round_store import RoundStore


class AnalysisTests(unittest.TestCase):
    def test_even_median(self):
        self.assertEqual(summary([1, 2, 3, 4])["median"], 2.5)

    def test_reject_invalid(self):
        for value in ("nan", "inf", "-1", "0", "bad"):
            with self.assertRaises(ValueError):
                validate(value)

    def test_walk_forward_uses_prior_rounds(self):
        result = walk_forward([1, 1, 1, 1, 1, 10])
        self.assertEqual(result["evaluated"], 1)
        self.assertEqual(result["rolling_mae"], 9)

    def test_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rounds.csv"
            path.write_text("multiplier\\n1.25\\n2.50\\n".replace("\\n", "\n"))
            self.assertEqual(read_csv(path), [1.25, 2.5])

    def test_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rounds.json"
            RoundStore(path).add(1.25)
            self.assertEqual(RoundStore(path).rounds, [1.25])


if __name__ == "__main__":
    unittest.main()
