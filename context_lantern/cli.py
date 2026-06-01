"""CLI entry point.

Subcommands:
  run      — Main pipeline: measure -> decide -> encode
  doctor   — Layered diagnostics
  status   — Show current state and token info
  install  — Generate and execute install steps for a host
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from context_lantern.core.models import Decision
from context_lantern.core.state import StateStore
from context_lantern.core.decide import make_decision, DEFAULT_THRESHOLD
from context_lantern.core.encode import to_debug_json
from context_lantern.core.measure import read_stdin_payload, read_payload_file


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add arguments shared across subcommands."""
    parser.add_argument(
        "--adapter", "-a", required=True, help="Adapter name (codex, cursor, ...)"
    )


def cmd_run(args: argparse.Namespace) -> int:
    """Run the measure -> decide -> encode pipeline."""
    from context_lantern.adapters import get_adapter

    adapter = get_adapter(args.adapter)

    # --- Read payload ---
    if args.stdin_file:
        payload = read_payload_file(Path(args.stdin_file).expanduser())
    else:
        payload = read_stdin_payload()

    # --- Measure (Adapter) ---
    measure = adapter.measure(payload, args)
    if measure is None:
        if args.debug:
            print(json.dumps({"status": "no_measurement"}, ensure_ascii=False))
        return 0

    # --- Debug mode: skip encode, show measure+decide ---
    threshold = args.threshold
    state = None if args.no_state else StateStore(Path(args.state_file))

    decision = make_decision(measure, threshold, state)

    if args.debug:
        debug = {
            "status": decision.decision.value,
            "adapter": args.adapter,
            "session_id": payload.get("session_id", ""),
            "dedup_key": measure.dedup_key,
            "loop_prevention": measure.loop_prevention,
            "transcript": measure.meta.get("transcript"),
            "line": measure.meta.get("line"),
            "input_tokens": measure.snapshot.input_tokens,
            "cached_input_tokens": measure.snapshot.cached_input_tokens,
            "total_tokens": measure.snapshot.total_tokens,
            "threshold": threshold,
            "source": measure.snapshot.source,
            "already_reminded": decision.already_reminded,
            "stop_hook_active": measure.loop_prevention,
        }
        print(json.dumps(debug, ensure_ascii=False))
        return 0

    # --- Encode (Adapter) ---
    output = adapter.encode(decision)
    if output:
        print(output)

    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Run layered diagnostics."""
    from context_lantern.doctor.checks import run_checks

    return run_checks(args)


def cmd_status(args: argparse.Namespace) -> int:
    """Show current state and latest token info."""
    state_path = Path(args.state_file)
    state = StateStore(state_path)
    entries = state.all_entries()

    if not entries:
        print("No reminders recorded yet.")
        return 0

    print(f"State file: {state_path}")
    print(f"Entries: {len(entries)}\n")
    for key, entry in entries.items():
        print(f"  {key}:")
        print(f"    reminded:  {entry.get('reminded')}")
        print(f"    tokens:    {entry.get('input_tokens')}")
        print(f"    threshold: {entry.get('threshold')}")
        print(f"    source:    {entry.get('source')}")
        print(f"    at:        {entry.get('at')}")
        print()

    return 0


def cmd_install(args: argparse.Namespace) -> int:
    """Generate and execute install steps."""
    from context_lantern.transports.install import run_install

    return run_install(args)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="context_lantern",
        description="Context Lantern — session context reminder tool.",
    )
    sub = parser.add_subparsers(dest="command")

    # --- run ---
    p_run = sub.add_parser("run", help="Run measure -> decide -> encode pipeline")
    _add_common_args(p_run)
    p_run.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    p_run.add_argument("--state-file", default=str(Path.home() / ".context-lantern" / "state.json"))
    p_run.add_argument("--no-state", action="store_true")
    p_run.add_argument("--transcript-path", type=Path)
    p_run.add_argument("--codex-home", type=Path)
    p_run.add_argument("--cursor-home", type=Path)
    p_run.add_argument("--stdin-file", type=str, help="Read payload from file instead of stdin")
    p_run.add_argument("--debug", action="store_true")

    # --- doctor ---
    p_doc = sub.add_parser("doctor", help="Run layered diagnostics")
    _add_common_args(p_doc)
    p_doc.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)

    # --- status ---
    p_status = sub.add_parser("status", help="Show current state")
    _add_common_args(p_status)
    p_status.add_argument("--state-file", default=str(Path.home() / ".context-lantern" / "state.json"))

    # --- install ---
    p_install = sub.add_parser("install", help="Install hook for a host")
    _add_common_args(p_install)
    p_install.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    dispatch = {
        "run": cmd_run,
        "doctor": cmd_doctor,
        "status": cmd_status,
        "install": cmd_install,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)
