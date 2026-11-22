"""Offline event timing report for the sanitized local capture log."""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def build_report(path):
    events = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    rounds = {}
    for event in events:
        rid = event.get("l")
        if not isinstance(rid, int):
            continue
        row = rounds.setdefault(rid, {"round_id": rid})
        target = event.get("target")
        if target in ("OnStart", "OnCrash", "OnStage"):
            row[target] = event.get("received_at_utc")
        if target == "OnCrash":
            row["final_multiplier"] = event.get("f")
    output = []
    for row in rounds.values():
        if "OnStart" in row and "OnCrash" in row:
            start = datetime.fromisoformat(row["OnStart"])
            end = datetime.fromisoformat(row["OnCrash"])
            row["flight_seconds_observed"] = round((end - start).total_seconds(), 3)
        output.append(row)
    return {
        "event_counts": dict(Counter(e.get("target") for e in events)),
        "rounds": output,
        "notes": [
            "Received timestamps are local observer timestamps, not server event times.",
            "The capture does not measure the on-screen explosion animation.",
            "A crash value seen at OnCrash does not reveal the next round's result.",
        ],
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--output", default="event_report.json")
    a = p.parse_args()
    Path(a.output).write_text(json.dumps(build_report(a.input), indent=2), encoding="utf-8")
    print("Wrote", a.output)
