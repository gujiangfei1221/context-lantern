"""Core encode utilities.

Encoder Protocol and shared helpers. Each Adapter implements its own
Encoder that translates a ReminderDecision into host-specific JSON.

Rule: stdout only carries host-recognized JSON.
      Human-readable logs go to stderr.
"""

from __future__ import annotations

import json
from typing import Protocol

from context_lantern.core.models import ReminderDecision


class Encoder(Protocol):
    """Protocol for host-specific output encoding."""

    def encode(self, decision: ReminderDecision) -> str:
        """Encode a decision into host-specific stdout JSON.

        Returns the exact string to print to stdout.
        Must be valid JSON that the host understands.
        For SILENT decisions, return empty string (no output).
        """
        ...


def to_debug_json(decision: ReminderDecision) -> str:
    """Encode a decision as debug JSON (for --debug mode).

    This is host-agnostic and goes to stdout in debug mode,
    bypassing the host-specific encoder.
    """
    return json.dumps(
        {
            "status": decision.decision.value,
            "input_tokens": decision.snapshot.input_tokens,
            "cached_input_tokens": decision.snapshot.cached_input_tokens,
            "total_tokens": decision.snapshot.total_tokens,
            "threshold": decision.threshold,
            "source": decision.snapshot.source,
            "already_reminded": decision.already_reminded,
            "message": decision.message,
        },
        ensure_ascii=False,
    )
