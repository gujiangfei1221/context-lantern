"""Windsurf stop hook adapter (skeleton).

Host capability (to be verified):
- Event: TBD
- Token source: TBD
- Loop prevention: TBD
- Output: TBD
- Dedup key: TBD

This adapter is a placeholder. Fill in the capability matrix
when Windsurf's hook system is researched and tested.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from context_lantern.core.models import (
    Decision,
    MeasureResult,
    ReminderDecision,
    TokenSnapshot,
)
from context_lantern.adapters import register_adapter


@register_adapter
class WindsurfStopAdapter:
    """Adapter for Windsurf stop hook (skeleton, not yet functional)."""

    @property
    def host_name(self) -> str:
        return "windsurf"

    @property
    def display_name(self) -> str:
        return "Windsurf"

    def measure(
        self, payload: dict[str, Any], args: argparse.Namespace
    ) -> MeasureResult | None:
        # TODO: Research Windsurf hook payload schema.
        # TODO: Determine token source priority.
        # TODO: Determine dedup key strategy.
        # TODO: Determine loop prevention flag.
        self.log("Windsurf adapter not yet implemented. Returning None.")
        return None

    def encode(self, decision: ReminderDecision) -> str:
        if decision.decision == Decision.SILENT:
            return ""

        # TODO: Research Windsurf's expected output schema.
        # Placeholder: same as generic JSON.
        return json.dumps(
            {"message": decision.message},
            ensure_ascii=False,
        )

    def log(self, message: str) -> None:
        print(f"[Context Lantern:windsurf] {message}", file=sys.stderr)
