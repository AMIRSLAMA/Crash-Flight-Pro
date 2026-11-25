import unittest
from pre_round_audit import audit, explicit_candidates

class AuditTests(unittest.TestCase):
    def test_only_semantic_multiplier_fields_are_candidates(self):
        event = {"target":"OnBetting","f":2.5,"numericPaths":[{"path":"$.q[0].v","value":2.5}]}
        self.assertEqual(explicit_candidates(event), [("f", 2.5)])

    def test_prestart_candidate_matches_later_crash(self):
        events = [
            {"target":"OnBetting","roundId":"r1","receivedAt":1000,"metrics":{"multiplier":2.25}},
            {"target":"OnStart","roundId":"r1","receivedAt":1500},
            {"target":"OnCrash","roundId":"r1","receivedAt":3000,"f":2.25},
        ]
        result = audit(events)
        self.assertEqual(result["roundsWithPreStartCandidate"], 1)
        self.assertEqual(result["matches"], 1)

    def test_post_start_value_is_not_prestart_candidate(self):
        events = [
            {"target":"OnStart","roundId":"r2","receivedAt":1000},
            {"target":"OnBetting","roundId":"r2","receivedAt":1200,"f":3.0},
            {"target":"OnCrash","roundId":"r2","receivedAt":3000,"f":3.0},
        ]
        result = audit(events)
        self.assertEqual(result["roundsWithPreStartCandidate"], 0)

    def test_missing_onstart_is_not_proven_prestart(self):
        events = [
            {"target":"OnBetting","roundId":"r3","receivedAt":1000,"f":2.0},
            {"target":"OnCrash","roundId":"r3","receivedAt":3000,"f":2.0},
        ]
        result = audit(events)
        self.assertEqual(result["roundsWithPreStartCandidate"], 0)

    def test_onstage_ln_can_link_round(self):
        events = [
            {"target":"OnStage","ln":7,"receivedAt":1000,"metrics":{"crash":1.8}},
            {"target":"OnCrash","roundId":"7","receivedAt":3000,"f":1.8},
        ]
        result = audit(events)
        self.assertEqual(result["matches"], 1)

if __name__ == "__main__":
    unittest.main()
