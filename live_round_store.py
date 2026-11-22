"""Persist completed live crash rounds by round ID, separately from manual history."""
import json
from pathlib import Path
from analysis_engine import validate


class LiveRoundStore:
    def __init__(self, path):
        self.path = Path(path)
        self.by_id = {}
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Live round archive must be an object")
            for key, value in data.items():
                self.by_id[str(key)] = validate(value)

    def add_event(self, event):
        if event.get("target") != "OnCrash":
            return False
        round_id = event.get("l")
        if round_id is None or isinstance(round_id, bool) or str(round_id).strip() == "":
            return False
        try:
            multiplier = validate(event.get("f"))
        except (ValueError, TypeError):
            return False
        key = str(round_id)
        if key in self.by_id:
            return False
        self.by_id[key] = multiplier
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.by_id, indent=2), encoding="utf-8")
        temporary.replace(self.path)
        return True

    @property
    def values(self):
        return list(self.by_id.values())

    @property
    def count(self):
        return len(self.by_id)
