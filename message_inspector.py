"""Inspect redacted, user-provided Crash message exports offline.

Input: JSON Lines with timestamp, direction, payload. No network access,
browser injection, interception, authentication or wagering.
"""
import argparse
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

SENSITIVE = re.compile(r"(token|cookie|authorization|password|secret|session|jwt|key)", re.I)
EVENT = re.compile(r"(start|begin|round|crash|end|finish|result|multiplier)", re.I)


def describe(value, depth=0):
    if depth > 4:
        return "<nested>"
    if isinstance(value, dict):
        return {str(k): ("<redacted>" if SENSITIVE.search(str(k)) else describe(v, depth + 1))
                for k, v in value.items()}
    if isinstance(value, list):
        return {"type": "array", "length": len(value),
                "sample_shape": describe(value[0], depth + 1) if value else None}
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        return "number"
    return type(value).__name__


def inspect(path):
    counts = Counter()
    events = []
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            payload = row.get("payload")
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {"unparsed_text": "<omitted>"}
            shape = describe(payload)
            counts[json.dumps(shape, sort_keys=True)] += 1
            labels = [k for k in payload if EVENT.search(k)] if isinstance(payload, dict) else []
            if labels:
                events.append({"timestamp": row.get("timestamp"),
                               "direction": row.get("direction"),
                               "event_keys": labels})
    return {"message_shapes": [{"count": count, "shape": json.loads(shape)}
                                for shape, count in counts.most_common()],
            "candidate_events": events[:200],
            "warning": "Timing alone does not establish knowledge before a round begins."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", help="Redacted message export, one JSON object per line")
    parser.add_argument("--output", default="message_report.json")
    args = parser.parse_args()
    report = inspect(args.jsonl)
    Path(args.output).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report written to {args.output}")
