import unittest
from pre_crash_audit import PreCrashAudit


class PreCrashAuditTests(unittest.TestCase):
    def test_no_guessed_result(self):
        audit = PreCrashAudit()
        audit.observe({"target": "OnStage", "l": 4, "ln": 5})
        self.assertEqual(audit.latest, "Advance crash X: NOT FOUND")

    def test_early_field_requires_matching_crash(self):
        audit = PreCrashAudit()
        audit.observe({"target": "OnStage", "l": 5, "f": 2.25})
        self.assertIn("Unverified", audit.latest)
        audit.observe({"target": "OnCrash", "l": 4, "f": 2.25})
        self.assertEqual(audit.matches, 0)
        audit.observe({"target": "OnCrash", "l": 5, "f": 2.25})
        self.assertEqual(audit.matches, 1)

    def test_post_start_candidate_not_accepted(self):
        audit = PreCrashAudit()
        audit.observe({"target": "OnStart", "l": 6})
        audit.observe({"target": "OnBetting", "l": 6, "f": 3})
        self.assertEqual(audit.candidates, {})

    def test_mismatch_not_reported_as_success(self):
        audit = PreCrashAudit()
        audit.observe({"target": "OnStage", "l": 7, "f": 3})
        audit.observe({"target": "OnCrash", "l": 7, "f": 4})
        self.assertEqual(audit.matches, 0)
        self.assertEqual(audit.mismatches, 1)


if __name__ == "__main__":
    unittest.main()
