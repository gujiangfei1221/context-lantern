"""Core state management for reminder deduplication.

One JSON file, keyed by dedup_key. Core doesn't care how the key was computed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass
from typing import Any


DEFAULT_STATE_PATH = Path.home() / ".context-lantern" / "state.json"


@dataclass
class StateEntry:
    """One entry in the state file."""

    reminded: bool
    input_tokens: int
    threshold: int
    source: str = "unknown"
    at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "reminded": self.reminded,
            "input_tokens": self.input_tokens,
            "threshold": self.threshold,
            "source": self.source,
            "at": self.at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StateEntry:
        return cls(
            reminded=bool(data.get("reminded")),
            input_tokens=int(data.get("input_tokens") or 0),
            threshold=int(data.get("threshold") or 0),
            source=str(data.get("source") or "unknown"),
            at=str(data.get("at") or ""),
        )


class StateStore:
    """JSON-backed state store for reminder deduplication.

    Dedup rule: a dedup_key is considered "already reminded" if
    reminded == True AND the stored input_tokens >= the current threshold.
    This ensures old entries from low-threshold tests don't block
    formal reminders at the real threshold.
    """

    def __init__(self, path: Path = DEFAULT_STATE_PATH) -> None:
        self._path = path
        self._data: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._data = raw if isinstance(raw, dict) else {}
        except Exception:
            self._data = {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def is_reminded(self, key: str, threshold: int) -> bool:
        """Check if this key was already reminded at or above threshold."""
        entry = self._data.get(key)
        if not entry or not entry.get("reminded"):
            return False
        return int(entry.get("input_tokens") or 0) >= threshold

    def mark_reminded(
        self,
        key: str,
        input_tokens: int,
        threshold: int,
        source: str = "unknown",
    ) -> None:
        """Record that this key has been reminded."""
        self._data[key] = {
            "reminded": True,
            "input_tokens": input_tokens,
            "threshold": threshold,
            "source": source,
            "at": datetime.now(timezone.utc).isoformat(),
        }
        self._save()

    def get_entry(self, key: str) -> dict[str, Any] | None:
        """Get raw state entry for debugging."""
        return self._data.get(key)

    def all_entries(self) -> dict[str, dict[str, Any]]:
        """Return all entries (for status command)."""
        return dict(self._data)
