"""GitHub Copilot stop hook adapter (skeleton).

Host capability (to be verified):
- Event: TBD
- Token source: TBD
- Loop prevention: TBD
- Output: TBD
- Dedup key: TBD

This adapter is a placeholder. Fill in the capability matrix
when Copilot's hook/extension system is researched and tested.
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
class CopilotStopAdapter:
    """Adapter for GitHub Copilot stop hook (skeleton, not yet functional)."""

    @property
    def host_name(self) -> str:
        return "copilot"

    @property
    def display_name(self) -> str:
        return "GitHub Copilot"

    def measure(
        self, payload: dict[str, Any], args: argparse.Namespace
    ) -> MeasureResult | None:
        # TODO: Research Copilot extension/hook payload schema.
        # TODO: Determine token source priority.
        # TODO: Determine dedup key strategy.
        # TODO: Determine loop prevention flag.
        self.log("Copilot adapter not yet implemented. Returning None.")
        return None

    def encode(self, decision: ReminderDecision) -> str:
        if decision.decision == Decision.SILENT:
            return ""

        # TODO: Research Copilot's expected output schema.
        # Placeholder: same as generic JSON.
        return json.dumps(
            {"message": decision.message},
            ensure_ascii=False,
        )

    def log(self, message: str) -> None:
        print(f"[Context Lantern:copilot] {message}", file=sys.stderr)
