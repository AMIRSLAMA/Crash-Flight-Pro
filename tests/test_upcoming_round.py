import unittest
from upcoming_round import UpcomingRound


class UpcomingRoundTests(unittest.TestCase):
    def test_id_is_not_multiplier(self):
        tracker = UpcomingRound()
        tracker.observe({"target": "OnStage", "l": 10, "ln": 11})
        self.assertEqual(tracker.round_id, 11)
        self.assertIsNone(tracker.final_multiplier)
        self.assertIn("UNKNOWN", tracker.display)

    def test_result_only_after_matching_crash(self):
        tracker = UpcomingRound()
        tracker.observe({"target": "OnStage", "l": 10, "ln": 11})
        tracker.observe({"target": "OnCrash", "l": 10, "f": 2.5})
        self.assertIsNone(tracker.final_multiplier)
        tracker.observe({"target": "OnCrash", "l": 11, "f": 3.7})
        self.assertEqual(tracker.final_multiplier, 3.7)
        self.assertIn("after crash", tracker.display)

    def test_new_round_clears_previous_result(self):
        tracker = UpcomingRound()
        tracker.observe({"target": "OnStage", "ln": 11})
        tracker.observe({"target": "OnCrash", "l": 11, "f": 3})
        tracker.observe({"target": "OnStage", "ln": 12})
        self.assertIsNone(tracker.final_multiplier)
        self.assertIn("UNKNOWN", tracker.display)


if __name__ == "__main__":
    unittest.main()
