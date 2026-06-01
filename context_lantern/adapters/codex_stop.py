"""Codex Stop hook adapter.

Migrated from the original codex_stop_hook.py. Behavior is identical
but now delegates business logic to Core.

Host capability:
- Event: Stop
- Token source: transcript JSONL (token_count entries)
- Loop prevention: stop_hook_active in payload
- Output: {"decision": "block", "reason": "..."}
- Dedup key: rollout id from transcript filename
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
    extract_dedup_key_from_filename,
    parse_transcript_token_count,
)
from context_lantern.adapters import register_adapter


CODEX_HOME = Path.home() / ".codex"
HANDOFF_SKILL_PATH = "/Users/gujiangfei/.codex/skills/session-handoff/SKILL.md"


@register_adapter
class CodexStopAdapter:
    """Adapter for OpenAI Codex Stop hook."""

    @property
    def host_name(self) -> str:
        return "codex"

    @property
    def display_name(self) -> str:
        return "OpenAI Codex"

    def measure(
        self, payload: dict[str, Any], args: argparse.Namespace
    ) -> MeasureResult | None:
        # Resolve transcript path.
        transcript_value = getattr(args, "transcript_path", None) or payload.get(
            "transcript_path"
        )
        codex_home = getattr(args, "codex_home", None) or CODEX_HOME

        if transcript_value:
            transcript = Path(transcript_value).expanduser()
        else:
            transcript = discover_latest_transcript(
                [codex_home / "sessions", codex_home / "archived_sessions"]
            )

        if not transcript or not transcript.exists():
            return None

        # Parse token count from transcript.
        snapshot = parse_transcript_token_count(transcript)
        if snapshot is None:
            return None

        # Build dedup key from transcript filename.
        session_id = str(payload.get("session_id") or "")
        dedup_key = extract_dedup_key_from_filename(
            transcript.name, fallback=session_id or str(transcript)
        )

        # Loop prevention flag.
        loop_prevention = bool(payload.get("stop_hook_active"))

        return MeasureResult(
            snapshot=snapshot,
            dedup_key=dedup_key,
            loop_prevention=loop_prevention,
            meta={
                "transcript": str(transcript),
                "session_id": session_id,
            },
        )

    def encode(self, decision: ReminderDecision) -> str:
        if decision.decision == Decision.SILENT:
            return ""

        message = (
            f"\u5f53\u524d\u4f1a\u8bdd\u672c\u8f6e input \u5df2\u7ea6 "
            f"{decision.snapshot.input_tokens // 1000}k\uff0c\u5efa\u8bae\u590d\u5236\u4e0b\u9762\u8fd9\u884c\u53d1\u9001\uff0c"
            "\u751f\u6210\u4ea4\u63a5\u4fe1\u606f\u540e\u5f00\u65b0\u4f1a\u8bdd\u7ee7\u7eed\uff1a\n\n"
            f"[$session-handoff]({HANDOFF_SKILL_PATH})"
        )
        return json.dumps(
            {"decision": "block", "reason": message},
            ensure_ascii=False,
        )

    def log(self, message: str) -> None:
        print(f"[Context Lantern:codex] {message}", file=sys.stderr)



