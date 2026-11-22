"""Offline timeline of sanitized SignalR events from the desktop observer.

Field meanings are based on the inspected *client* code in Crash-Game-Source:
OnStage.ln identifies the next stage (round), while OnCrash.f is the current
stage's final crash multiplier. OnRegistration.p is read only in ended states.
None of these fields alone establishes an early future result.
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def build_report(path):
    events = [
        json.loads(line) for line in
        Path(path).read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    rounds = {}
    for event in events:
        if not isinstance(event, dict):
            continue
        rid = event.get("l")
        if not isinstance(rid, (int, str)) or isinstance(rid, bool) or not str(rid):
            continue
        row = rounds.setdefault(str(rid), {
            "round_id": str(rid),
            "observed_events": [],
        })
        target = event.get("target")
        if target not in {"OnRegistration", "OnStage", "OnBetting", "OnStart", "OnCrash"}:
            continue
        timestamp = event.get("received_at_utc")
        row["observed_events"].append({"type": target, "received_at_utc": timestamp})
        if target in ("OnStart", "OnCrash", "OnStage"):
            row[target] = timestamp
        if target == "OnStage" and event.get("ln") is not None:
            row["next_round_id_announced"] = str(event["ln"])
        if target == "OnRegistration":
            state = event.get("s")
            row["registration_stage"] = state
            if state in (4, 5) and event.get("p") is not None:
                row["completed_result_on_reconnection"] = event["p"]
        if target == "OnBetting" and event.get("a") is not None:
            row["advertised_betting_window_ms"] = event["a"]
        if target == "OnCrash":
            row["final_multiplier"] = event.get("f")
            row["final_result_first_observed_at"] = timestamp

    output = []
    for row in rounds.values():
        if row.get("OnStart") and row.get("OnCrash"):
            try:
                start = datetime.fromisoformat(row["OnStart"])
                end = datetime.fromisoformat(row["OnCrash"])
                row["flight_seconds_observed"] = round(
                    (end - start).total_seconds(), 3
                )
            except (ValueError, TypeError):
                pass
        output.append(row)
    return {
        "event_counts": dict(Counter(
            e.get("target") for e in events if isinstance(e, dict)
        )),
        "rounds": output,
        "schema_evidence": {
            "OnStage.ln": "next round ID; not a multiplier",
            "OnCrash.f": "completed crash multiplier for OnCrash.l",
            "OnRegistration.p": "client reads as result in ended/closed state only",
        },
        "notes": [
            "Observer timestamps mark local message receipt, not game server generation.",
            "No on-screen animation timing is measured.",
            "Seeing OnCrash.f does not establish advance knowledge of the next round.",
            "This is a frontend protocol interpretation, not server RNG source code.",
        ],
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("input")
    p.add_argument("--output", default="event_report.json")
    a = p.parse_args()
    Path(a.output).write_text(
        json.dumps(build_report(a.input), indent=2), encoding="utf-8"
    )
    print("Wrote", a.output)
