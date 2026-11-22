"""Local-only historical round persistence. No credentials or browser cookies."""
import json
from pathlib import Path
from analysis_engine import validate


class RoundStore:
    def __init__(self, path):
        self.path = Path(path)
        self.rounds = []
        self.load()

    def load(self):
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("Round store must be a list")
        self.rounds = [validate(value) for value in raw]

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.rounds, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def add(self, value):
        self.rounds.append(validate(value))
        self.save()

    def import_values(self, values):
        # Append rather than deduplicate by multiplier: identical results can be real.
        self.rounds.extend(validate(value) for value in values)
        self.save()

    def clear(self):
        self.rounds = []
        self.save()
