"""Audit explicit pre-start crash-X fields against actual results.

A candidate is NOT a prediction or a verified advance disclosure until
matched against a later OnCrash for the same round.
"""
import math


class PreCrashAudit:
    def __init__(self):
        self.started = set()
        self.candidates = {}
        self.matches = 0
        self.mismatches = 0
        self.latest = "Advance crash X: NOT FOUND"

    @staticmethod
    def valid_x(value):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 1

    def observe(self, event):
        target = event.get("target")
        round_id = event.get("l")
        if not isinstance(round_id, (str, int)) or isinstance(round_id, bool):
            return
        if target == "OnStart":
            self.started.add(round_id)
        elif target in ("OnStage", "OnBetting"):
            x = event.get("f")
            if round_id not in self.started and self.valid_x(x):
                self.candidates[round_id] = float(x)
                self.latest = f"Unverified early field: round {round_id} = {x}x (awaiting crash)"
        elif target == "OnCrash":
            x = event.get("f")
            if round_id in self.candidates and self.valid_x(x):
                candidate = self.candidates.pop(round_id)
                if math.isclose(candidate, float(x), rel_tol=0, abs_tol=0.00001):
                    self.matches += 1
                    self.latest = f"Confirmed historical match: round {round_id} = {x}x; matches {self.matches}"
                else:
                    self.mismatches += 1
                    self.latest = f"Early field mismatch on round {round_id}; matches {self.matches}, mismatches {self.mismatches}"
            self.started.discard(round_id)
