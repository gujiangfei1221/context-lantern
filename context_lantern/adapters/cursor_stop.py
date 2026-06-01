"""Cursor stop hook adapter.

Host capability:
- Event: stop
- Token source: payload cache_* fields (primary), payload input_tokens (fallback)
- Loop prevention: loop_count > 0
- Output: {"followup_message": "..."}
- Dedup key: conversation_id or transcript stem

Note: Cursor's payload schema may differ. This adapter is based on
observed behavior and should be verified against real Cursor payloads.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from context_lantern.core.models import (
    Decision,
    MeasureResult,
    ReminderDecision,
    TokenSnapshot,
)
from context_lantern.core.measure import (
    discover_latest_transcript,
    parse_transcript_token_count,
    resolve_tokens,
)
from context_lantern.adapters import register_adapter


CURSOR_HOME = Path.home() / ".cursor"


@register_adapter
class CursorStopAdapter:
    """Adapter for Cursor stop hook."""

    @property
    def host_name(self) -> str:
        return "cursor"

    @property
    def display_name(self) -> str:
        return "Cursor"

    def measure(
        self, payload: dict[str, Any], args: argparse.Namespace
    ) -> MeasureResult | None:
        # --- Token resolution with fallback chain ---
        # Priority 1: payload cache-aware fields (Cursor may provide these)
        payload_cached = int(payload.get("cache_read_tokens") or payload.get("cache_read_input_tokens") or 0)
        payload_input = int(payload.get("input_tokens") or 0)
        payload_total = int(payload.get("total_tokens") or 0)
        payload_ctx = int(payload.get("model_context_window") or 0)

        sources: list[tuple[str, int, int, int, int]] = []

        if payload_input > 0 or payload_cached > 0:
            # Cache-aware: subtract cached from total input if both present
            effective_input = max(payload_input - payload_cached, 0) if payload_cached else payload_input
            sources.append(
                ("payload_cache", effective_input, payload_cached, payload_total, payload_ctx)
            )

        # Priority 2: transcript fallback
        cursor_home = getattr(args, "cursor_home", None) or CURSOR_HOME
        transcript_roots = [cursor_home / "sessions", cursor_home / "archived_sessions"]
        transcript_value = getattr(args, "transcript_path", None)
        transcript = (
            Path(transcript_value).expanduser()
            if transcript_value
            else discover_latest_transcript(transcript_roots)
        )

        if transcript and transcript.exists():
            ts_snapshot = parse_transcript_token_count(transcript)
            if ts_snapshot:
                sources.append(
                    (
                        "transcript",
                        ts_snapshot.input_tokens,
                        ts_snapshot.cached_input_tokens,
                        ts_snapshot.total_tokens,
                        ts_snapshot.model_context_window,
                    )
                )

        snapshot = resolve_tokens(sources)
        if snapshot is None:
            return None

        # --- Dedup key ---
        conversation_id = str(payload.get("conversation_id") or "")
        if conversation_id:
            dedup_key = conversation_id
        elif transcript:
            dedup_key = transcript.stem
        else:
            dedup_key = "cursor-unknown"

        # --- Loop prevention ---
        loop_count = int(payload.get("loop_count") or 0)
        loop_prevention = loop_count > 0

        return MeasureResult(
            snapshot=snapshot,
            dedup_key=dedup_key,
            loop_prevention=loop_prevention,
            meta={
                "transcript": str(transcript) if transcript else None,
                "conversation_id": conversation_id,
                "loop_count": loop_count,
            },
        )

    def encode(self, decision: ReminderDecision) -> str:
        if decision.decision == Decision.SILENT:
            return ""

        message = (
            f"Session input ~{decision.snapshot.input_tokens // 1000}k. "
            "Consider starting a new session with a handoff prompt."
        )
        return json.dumps(
            {"followup_message": message},
            ensure_ascii=False,
        )

    def log(self, message: str) -> None:
        print(f"[Context Lantern:cursor] {message}", file=sys.stderr)
