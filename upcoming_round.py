"""Track announced next round ID and its actual result without predicting it."""


class UpcomingRound:
    def __init__(self):
        self.round_id = None
        self.final_multiplier = None

    def observe(self, event):
        target = event.get("target")
        if target == "OnStage":
            next_id = event.get("ln")
            if isinstance(next_id, int) and not isinstance(next_id, bool) and next_id >= 0:
                if next_id != self.round_id:
                    self.round_id = next_id
                    self.final_multiplier = None
        elif target == "OnCrash":
            if self.round_id is not None and event.get("l") == self.round_id:
                value = event.get("f")
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    import math
                    if math.isfinite(value) and value >= 1:
                        self.final_multiplier = float(value)

    @property
    def display(self):
        if self.round_id is None:
            return "Next round ID: waiting for OnStage | Crash X: UNKNOWN"
        if self.final_multiplier is None:
            return f"Announced round ID: {self.round_id} | Crash X: UNKNOWN (not received)"
        return f"Round ID: {self.round_id} | Actual crash: {self.final_multiplier:.2f}x (received after crash)"
