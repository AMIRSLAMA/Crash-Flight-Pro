"""Pure historical statistics and walk-forward evaluation (no future-result prediction)."""
import csv
import math
import statistics
from pathlib import Path


def validate(value):
    number = float(str(value).strip().rstrip("xX"))
    if not math.isfinite(number) or number < 1:
        raise ValueError("Multiplier must be finite and >= 1")
    return number


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or "multiplier" not in reader.fieldnames:
            raise ValueError("CSV requires a 'multiplier' column")
        return [validate(row["multiplier"]) for row in reader]


def summary(rounds):
    if not rounds:
        return None
    recent = rounds[-30:]
    return {
        "count": len(rounds),
        "median": statistics.median(rounds),
        "recent_median": statistics.median(recent),
        "below_2": sum(v < 2 for v in rounds) / len(rounds),
        "at_least_2": sum(v >= 2 for v in rounds) / len(rounds),
        "minimum": min(rounds),
        "maximum": max(rounds),
    }


def walk_forward(rounds, window=30, minimum=5):
    """Evaluate a rolling historical median strictly against *later* observations.

    Returns MAE and a constant-median baseline for comparison; neither forecasts
    a random game's next outcome.
    """
    if len(rounds) <= minimum:
        return None
    errors = []
    baseline_errors = []
    for index in range(minimum, len(rounds)):
        history = rounds[max(0, index - window):index]
        estimate = statistics.median(history)
        baseline = statistics.median(rounds[:minimum])
        actual = rounds[index]
        errors.append(abs(estimate - actual))
        baseline_errors.append(abs(baseline - actual))
    return {
        "evaluated": len(errors),
        "rolling_mae": statistics.mean(errors),
        "baseline_mae": statistics.mean(baseline_errors),
    }
