import json
import tempfile
import unittest
from pathlib import Path

from live_round_store import LiveRoundStore


class LiveRoundStoreTests(unittest.TestCase):
    def test_add_crash_once_and_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "live_rounds.json"
            store = LiveRoundStore(path)
            self.assertTrue(store.add_event({"target": "OnCrash", "l": 50848151, "f": 6.51}))
            self.assertFalse(store.add_event({"target": "OnCrash", "l": 50848151, "f": 6.51}))
            self.assertEqual(store.count, 1)
            self.assertEqual(LiveRoundStore(path).values, [6.51])

    def test_ignore_nonfinal_and_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LiveRoundStore(Path(tmp) / "live_rounds.json")
            self.assertFalse(store.add_event({"target": "OnStart", "l": 1, "f": 2}))
            self.assertFalse(store.add_event({"target": "OnCrash", "l": 2, "f": "nan"}))
            self.assertFalse(store.add_event({"target": "OnCrash", "f": 3}))
            self.assertEqual(store.count, 0)

    def test_identical_multipliers_different_rounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = LiveRoundStore(Path(tmp) / "live_rounds.json")
            self.assertTrue(store.add_event({"target": "OnCrash", "l": 1, "f": 2.0}))
            self.assertTrue(store.add_event({"target": "OnCrash", "l": 2, "f": 2.0}))
            self.assertEqual(store.count, 2)


if __name__ == "__main__":
    unittest.main()
