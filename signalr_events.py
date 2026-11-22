"""Parse exported SignalR messages offline. Never connects to the game.

Supports pasted DevTools frames (JSON followed by ASCII record separator 0x1e)
or JSONL rows with timestamp and payload. Do not include credentials or cookies.
"""
import json
from datetime import datetime, timezone
from pathlib import Path


def parse_frame(raw):
    if isinstance(raw, dict):
        return [raw]
    frames = []
    for part in str(raw).split("\x1e"):
        part = part.strip()
        if not part:
            continue
        try:
            obj = json.loads(part)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            frames.append(obj)
    return frames


def extract_events(text):
    events = []
    for line in text.splitlines():
        # Accept JSONL envelopes or bare SignalR frame lines.
        raw = line.strip()
        if not raw:
            continue
        try:
            envelope = json.loads(raw)
        except json.JSONDecodeError:
            envelope = {"payload": raw}
        if isinstance(envelope, dict) and "payload" in envelope:
            timestamp = envelope.get("timestamp")
            frames = parse_frame(envelope["payload"])
        else:
            timestamp = None
            frames = parse_frame(envelope)
        for frame in frames:
            target = frame.get("target")
            if target not in {"OnCrash", "OnStage", "OnBetting", "OnStart", "OnBets", "OnProfits"}:
                continue
            args = frame.get("arguments", [])
            payload = args[0] if isinstance(args, list) and args and isinstance(args[0], dict) else {}
            event = {"target": target, "received_at": timestamp, "round_id": payload.get("l")}
            if target == "OnCrash":
                event["final_multiplier"] = payload.get("f")
            if target == "OnStage":
                event["next_round_field_ln"] = payload.get("ln")
            if target == "OnBetting":
                event["betting_window_ms"] = payload.get("a")
            if target == "OnBets":
                event["bet_count"] = payload.get("n")
            if "ts" in payload:
                event["server_timestamp_ms"] = payload["ts"]
                try:
                    event["server_time_utc"] = datetime.fromtimestamp(
                        payload["ts"] / 1000, tz=timezone.utc
                    ).isoformat()
                except (ValueError, OverflowError, TypeError):
                    pass
            events.append(event)
    return events


def summarize(events):
    starts = {}
    crashes = {}
    for event in events:
        rid = event["round_id"]
        if event["target"] == "OnStart":
            starts[rid] = event
        if event["target"] == "OnCrash":
            crashes[rid] = event
    return {
        "events": events,
        "completed_rounds": [
            {"round_id": rid, "final_multiplier": crash.get("final_multiplier"),
             "start_seen_in_export": rid in starts,
             "note": "Crash value belongs to the same round_id, not the next one."}
            for rid, crash in crashes.items()
        ],
        "warning": "A message received before the UI animation is not proof of a next-round outcome.",
    }


def analyze_file(path, output="signalr_report.json"):
    report = summarize(extract_events(Path(path).read_text(encoding="utf-8")))
    Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Text or JSONL export of redacted SignalR frames")
    parser.add_argument("--output", default="signalr_report.json")
    args = parser.parse_args()
    result = analyze_file(args.file, args.output)
    print(f"Parsed {len(result['events'])} events; report saved to {args.output}")
