import json
import tempfile
import unittest
from pathlib import Path

from event_report import build_report


class SourceSchemaReportTests(unittest.TestCase):
    def test_next_id_not_mistaken_for_multiplier(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            events = [
                {"target": "OnStage", "l": 10, "ln": 11,
                 "received_at_utc": "2026-11-22T12:00:00+00:00"},
                {"target": "OnStart", "l": 10,
                 "received_at_utc": "2026-11-22T12:00:10+00:00"},
                {"target": "OnCrash", "l": 10, "f": 3.5,
                 "received_at_utc": "2026-11-22T12:00:12+00:00"},
            ]
            path.write_text(
                "\n".join(json.dumps(x) for x in events),
                encoding="utf-8",
            )
            data = build_report(path)
            row = data["rounds"][0]
            self.assertEqual(row["next_round_id_announced"], "11")
            self.assertEqual(row["final_multiplier"], 3.5)
            self.assertEqual(row["flight_seconds_observed"], 2.0)
            self.assertNotIn("predicted_multiplier", row)

    def test_registration_result_only_after_ended(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "events.jsonl"
            records = [
                {"target": "OnRegistration", "l": 1, "s": 3},
                {"target": "OnRegistration", "l": 2, "s": 4, "p": 6.2},
            ]
            path.write_text(
                "\n".join(json.dumps(x) for x in records),
                encoding="utf-8",
            )
            data = build_report(path)
            self.assertNotIn("completed_result_on_reconnection", data["rounds"][0])
            self.assertEqual(data["rounds"][1]["completed_result_on_reconnection"], 6.2)


if __name__ == "__main__":
    unittest.main()
