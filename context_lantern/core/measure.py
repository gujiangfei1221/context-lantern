"""Core measure utilities.

These are shared helpers used by Adapters during the measure step.
The orchestration (which source to try first, fallback order) lives
in each Adapter. Core only provides the building blocks.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from context_lantern.core.models import TokenSnapshot


def parse_transcript_token_count(path: Path) -> TokenSnapshot | None:
    """Parse the latest token_count entry from a JSONL transcript.

    Works for Codex-style transcripts where each line is a JSON object
    with payload.type == "token_count".

    Returns the last token_count found, or None if the file has no such entries.
    """
    latest: dict[str, Any] | None = None
    line_no = 0
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            for line_no, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                payload = row.get("payload")
                if not isinstance(payload, dict) or payload.get("type") != "token_count":
                    continue
                info = payload.get("info")
                if not isinstance(info, dict):
                    continue
                usage = info.get("last_token_usage")
                if not isinstance(usage, dict):
                    continue
                latest = {
                    "line": line_no,
                    "input_tokens": int(usage.get("input_tokens") or 0),
                    "cached_input_tokens": int(usage.get("cached_input_tokens") or 0),
                    "total_tokens": int(usage.get("total_tokens") or 0),
                    "model_context_window": int(info.get("model_context_window") or 0),
                }
    except OSError:
        return None

    if latest is None:
        return None

    return TokenSnapshot(
        input_tokens=latest["input_tokens"],
        cached_input_tokens=latest["cached_input_tokens"],
        total_tokens=latest["total_tokens"],
        model_context_window=latest["model_context_window"],
        source="transcript",
    )


def resolve_tokens(
    sources: list[tuple[str, int, int, int, int]],
) -> TokenSnapshot | None:
    """Try multiple token sources in priority order.

    Each source is a tuple: (source_name, input_tokens, cached, total, context_window).
    Returns the first source with input_tokens > 0.

    Adapters build this list according to their host-specific priority.
    """
    for source_name, inp, cached, total, ctx in sources:
        if inp > 0:
            return TokenSnapshot(
                input_tokens=inp,
                cached_input_tokens=cached,
                total_tokens=total,
                model_context_window=ctx,
                source=source_name,
            )
    return None


def extract_dedup_key_from_filename(
    filename: str, fallback: str = ""
) -> str:
    """Extract a rollout-style id from a transcript filename.

    Matches patterns like: rollout-<model>-<date>-<hex-uuid>.jsonl
    Returns the uuid portion, or fallback if no match.
    """
    match = re.search(
        r"rollout-[^-]+-\d\d-\d\dT\d\d-\d\d-\d\d-([0-9a-f-]+)\.jsonl$",
        filename,
    )
    if match:
        return match.group(1)
    return fallback


def discover_latest_transcript(roots: list[Path]) -> Path | None:
    """Find the most recently modified .jsonl file under the given roots."""
    candidates: list[Path] = []
    for root in roots:
        if root.exists():
            candidates.extend(root.glob("**/*.jsonl"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def read_stdin_payload() -> dict[str, Any]:
    """Read and parse JSON from stdin. Returns {} on any failure."""
    import sys

    try:
        text = sys.stdin.read().strip()
        return json.loads(text) if text else {}
    except Exception:
        return {}


def read_payload_file(path: Path) -> dict[str, Any]:
    """Read and parse JSON from a file. Returns {} on any failure."""
    try:
        text = path.read_text(encoding="utf-8").strip()
        return json.loads(text) if text else {}
    except Exception:
        return {}
