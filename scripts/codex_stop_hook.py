#!/usr/bin/env python3
"""Warn once when a Codex session's latest input tokens exceed a threshold."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


DEFAULT_THRESHOLD = 120_000
DEFAULT_CODEX_HOME = Path.home() / ".codex"
DEFAULT_STATE_FILE = DEFAULT_CODEX_HOME / "session_guard_state.json"


def load_stdin_payload() -> dict[str, Any]:
    try:
        import sys

        text = sys.stdin.read().strip()
        return json.loads(text) if text else {}
    except Exception:
        return {}


def discover_latest_transcript(codex_home: Path) -> Path | None:
    roots = [codex_home / "sessions", codex_home / "archived_sessions"]
    candidates: list[Path] = []
    for root in roots:
        if root.exists():
            candidates.extend(root.glob("**/*.jsonl"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def find_latest_token_count(path: Path) -> dict[str, Any] | None:
    latest: dict[str, Any] | None = None
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
    return latest


def load_state(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def format_k(tokens: int) -> str:
    return f"{round(tokens / 1000)}k"


def state_key_for(session_id: str, transcript: Path) -> str:
    match = re.search(r"rollout-[^-]+-\d\d-\d\dT\d\d-\d\d-\d\d-([0-9a-f-]+)\.jsonl$", transcript.name)
    if match:
        return match.group(1)
    return session_id or str(transcript)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Codex Stop hook for session handoff reminders.")
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    parser.add_argument("--codex-home", type=Path, default=DEFAULT_CODEX_HOME)
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    parser.add_argument("--no-state", action="store_true", help="Do not suppress repeated reminders.")
    parser.add_argument("--transcript-path", type=Path, help="Override transcript path for tests.")
    parser.add_argument("--debug", action="store_true", help="Print a JSON debug object instead of hook output.")
    args = parser.parse_args(argv)

    payload = load_stdin_payload()
    session_id = str(payload.get("session_id") or "")
    stop_hook_active = bool(payload.get("stop_hook_active"))
    transcript_value = args.transcript_path or payload.get("transcript_path")
    transcript = Path(transcript_value).expanduser() if transcript_value else discover_latest_transcript(args.codex_home)

    if not transcript or not transcript.exists():
        if args.debug:
            print(json.dumps({"status": "no_transcript"}, ensure_ascii=False))
        return 0

    token_count = find_latest_token_count(transcript)
    if not token_count:
        if args.debug:
            print(json.dumps({"status": "no_token_count", "transcript": str(transcript)}, ensure_ascii=False))
        return 0

    input_tokens = int(token_count["input_tokens"])
    state_key = state_key_for(session_id, transcript)
    state = {} if args.no_state else load_state(args.state_file)
    state_entry = state.get(state_key, {})
    reminded = state_entry.get("reminded") is True and int(state_entry.get("input_tokens") or 0) >= args.threshold
    should_warn = input_tokens >= args.threshold and not reminded and not stop_hook_active

    if args.debug:
        print(
            json.dumps(
                {
                    "status": "warn" if should_warn else "silent",
                    "session_id": session_id,
                    "transcript": str(transcript),
                    "line": token_count["line"],
                    "input_tokens": input_tokens,
                    "threshold": args.threshold,
                    "already_reminded": reminded,
                    "stop_hook_active": stop_hook_active,
                },
                ensure_ascii=False,
            )
        )
        return 0

    if not should_warn:
        return 0

    if not args.no_state:
        state[state_key] = {
            "reminded": True,
            "input_tokens": input_tokens,
            "threshold": args.threshold,
            "transcript": str(transcript),
            "line": token_count["line"],
        }
        save_state(args.state_file, state)

    message = (
        f"当前会话本轮 input 已约 {format_k(input_tokens)}，建议复制下面这行发送，"
        "生成交接信息后开新会话继续：\n\n"
        "[$session-handoff](/Users/gujiangfei/.codex/skills/session-handoff/SKILL.md)"
    )
    print(json.dumps({"decision": "block", "reason": message}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
