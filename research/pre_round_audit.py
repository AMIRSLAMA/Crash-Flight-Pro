#!/usr/bin/env python3
"""Forensic audit of exported Crash Flight JSONL events.

This tool does NOT predict crash outcomes. It checks whether an explicit,
round-linked crash-like value was present before OnStart and whether it later
matched the OnCrash result. It deliberately avoids treating arbitrary numeric
telemetry (for example OnProfits points) as a prediction.
"""
from __future__ import annotations
import argparse, json, math, re
from collections import defaultdict
from pathlib import Path

VALUE_KEYS = re.compile(r"^(?:f|crash|crashx|crash_multiplier|multiplier|coef|coefficient|factor|result)$", re.I)
ROUND_TARGETS = {"OnStage", "OnBetting", "OnStart", "OnCrash", "OnProfits", "OnBets"}


def finite_multiplier(value):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= 1.0)


def event_round(event):
    rid = event.get("roundId")
    if rid is not None and str(rid):
        return str(rid)
    # OnStage's ln is often the announced upcoming round identifier.
    ln = event.get("ln")
    if event.get("target") == "OnStage" and ln is not None:
        return str(ln)
    return None


def explicit_candidates(event):
    """Return only semantically named multiplier fields, never generic numbers."""
    found = []
    if finite_multiplier(event.get("f")):
        found.append(("f", float(event["f"])))
    metrics = event.get("metrics")
    if isinstance(metrics, dict):
        for key, value in metrics.items():
            if VALUE_KEYS.match(str(key)) and finite_multiplier(value):
                found.append((f"metrics.{key}", float(value)))
    # numericPaths are intentionally not promoted to candidates: paths such as
    # $.q[0].v may be curve coordinates, not a crash result.
    return found


def load_events(path):
    events = []
    with Path(path).open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc
            if isinstance(item, dict) and item.get("target") in ROUND_TARGETS:
                events.append(item)
    events.sort(key=lambda e: e.get("receivedAt", 0))
    return events


def audit(events):
    rounds = defaultdict(list)
    unlinked = 0
    for event in events:
        rid = event_round(event)
        if rid is None:
            unlinked += 1
            continue
        rounds[rid].append(event)

    results = []
    for rid, records in rounds.items():
        records.sort(key=lambda e: e.get("receivedAt", 0))
        starts = [e.get("receivedAt", 0) for e in records if e.get("target") == "OnStart"]
        crashes = [e for e in records if e.get("target") == "OnCrash" and finite_multiplier(e.get("f"))]
        if not crashes:
            continue
        crash = crashes[-1]
        crash_time = crash.get("receivedAt", 0)
        actual = float(crash["f"])
        start_time = min((t for t in starts if t <= crash_time), default=None)
        if start_time is None:
            continue  # Without OnStart, we cannot prove that a value arrived pre-start.
        candidates = []
        for event in records:
            t = event.get("receivedAt", 0)
            if t >= crash_time:
                continue
            if start_time is not None and t >= start_time:
                continue
            if event.get("target") not in {"OnStage", "OnBetting"}:
                continue
            for source, value in explicit_candidates(event):
                candidates.append({"target": event.get("target"), "source": source,
                                   "value": value, "receivedAt": t})
        if candidates:
            chosen = candidates[-1]
            results.append({"roundId": rid, "actual": actual, "candidate": chosen["value"],
                            "source": chosen["source"], "event": chosen["target"],
                            "match": math.isclose(chosen["value"], actual, rel_tol=0, abs_tol=1e-6),
                            "leadMs": max(0, crash_time - chosen["receivedAt"])})
    matches = sum(1 for r in results if r["match"])
    return {"events": len(events), "linkedRounds": len(rounds), "unlinkedEvents": unlinked,
            "roundsWithPreStartCandidate": len(results), "matches": matches,
            "mismatches": len(results)-matches, "results": results}


def main():
    parser = argparse.ArgumentParser(description="Audit pre-start Crash event fields from Crash Flight JSONL")
    parser.add_argument("jsonl", help="Exported crash-flight-events.jsonl")
    parser.add_argument("--output", default="pre-round-audit-report.json")
    args = parser.parse_args()
    report = audit(load_events(args.jsonl))
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Events: {report['events']} | linked rounds: {report['linkedRounds']} | unlinked: {report['unlinkedEvents']}")
    print(f"Pre-start candidates: {report['roundsWithPreStartCandidate']} | exact matches: {report['matches']} | mismatches: {report['mismatches']}")
    if not report["results"]:
        print("No explicit round-linked multiplier candidate was found before OnStart.")
    print(f"Report saved: {args.output}")


if __name__ == "__main__":
    main()
