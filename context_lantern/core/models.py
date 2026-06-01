"""Core data models.

Core only knows these three concepts. It does not know which host
(Codex, Cursor, Windsurf, Copilot) is calling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True)
class TokenSnapshot:
    """Standardized token measurement snapshot.

    All host-specific differences are resolved in the Adapter layer
    before this structure is created.

    Attributes:
        input_tokens: Non-cached input tokens for this turn.
        cached_input_tokens: Cached input tokens (0 if source doesn't provide).
        total_tokens: Total tokens including output (0 if unavailable).
        model_context_window: Model's context window size (0 if unknown).
        source: Where the data came from. One of:
            "transcript" — parsed from transcript JSONL
            "payload" — extracted from stdin payload directly
            "payload_cache" — payload with cache-aware field priority
            "byte_estimate" — estimated from byte count
            "unknown" — fallback
    """

    input_tokens: int
    cached_input_tokens: int = 0
    total_tokens: int = 0
    model_context_window: int = 0
    source: str = "unknown"


@dataclass(frozen=True)
class MeasureResult:
    """Complete measurement result delivered by an Adapter to Core.

    Attributes:
        snapshot: The token snapshot.
        dedup_key: Deduplication key. Adapter computes it, Core only uses it.
            For Codex: rollout id from transcript filename.
            For Cursor: conversation_id or transcript stem.
        loop_prevention: Normalized host loop-prevention flag.
            Codex: stop_hook_active
            Cursor: loop_count > 0
            Adapter translates host-specific flags into this boolean.
        meta: Optional debug metadata (line numbers, raw fields, etc.).
    """

    snapshot: TokenSnapshot
    dedup_key: str
    loop_prevention: bool = False
    meta: dict = field(default_factory=dict)


class Decision(Enum):
    """Reminder decision outcome."""

    SILENT = "silent"
    WARN_ONCE = "warn_once"


@dataclass(frozen=True)
class ReminderDecision:
    """Core's output: what to do and why.

    Attributes:
        decision: SILENT or WARN_ONCE.
        snapshot: The token snapshot that triggered this decision.
        threshold: The threshold used for comparison.
        message: Human-readable reminder message (empty if SILENT).
        already_reminded: Whether this dedup_key was already reminded.
    """

    decision: Decision
    snapshot: TokenSnapshot
    threshold: int
    message: str = ""
    already_reminded: bool = False
