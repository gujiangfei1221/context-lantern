"""Doctor — layered diagnostics.

Runs checks layer by layer (Transport -> Adapter -> Core -> Encode).
Each check independently reports PASS / FAIL / SKIP so the user can
pinpoint which layer has the problem.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Any


@dataclass
class CheckResult:
    """Result of a single diagnostic check."""

    name: str
    layer: str
    status: str  # "PASS", "FAIL", "SKIP"
    message: str = ""


def _check_python_version() -> CheckResult:
    """Transport: Check Python version."""
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 10):
        return CheckResult("Python version", "Transport", "PASS", f"{version_str} >= 3.10")
    return CheckResult("Python version", "Transport", "FAIL", f"{version_str} < 3.10 required")


def _check_stdin_readable() -> CheckResult:
    """Transport: Check if stdin is readable."""
    try:
        if sys.stdin.isatty():
            return CheckResult("stdin readable", "Transport", "SKIP", "stdin is a TTY (no piped input)")
        data = sys.stdin.read(1)
        return CheckResult("stdin readable", "Transport", "PASS", f"first byte: {repr(data)}")
    except Exception as e:
        return CheckResult("stdin readable", "Transport", "FAIL", str(e))


def _check_adapter_loadable(adapter_name: str) -> CheckResult:
    """Adapter: Check if the adapter can be loaded."""
    try:
        from context_lantern.adapters import get_adapter
        adapter = get_adapter(adapter_name)
        return CheckResult("Adapter loadable", "Adapter", "PASS", f"{adapter.display_name}")
    except KeyError as e:
        return CheckResult("Adapter loadable", "Adapter", "FAIL", str(e))
    except Exception as e:
        return CheckResult("Adapter loadable", "Adapter", "FAIL", str(e))


def _check_measure(adapter_name: str) -> CheckResult:
    """Adapter: Check if measure works with a synthetic payload."""
    try:
        from context_lantern.adapters import get_adapter
        adapter = get_adapter(adapter_name)
        # Try with empty payload — may return None (no transcript), which is OK
        measure = adapter.measure({}, argparse.Namespace(transcript_path=None))
        if measure is None:
            return CheckResult("Measure (synthetic)", "Adapter", "SKIP", "No transcript/token data available (expected if none exists)")
        return CheckResult(
            "Measure (synthetic)",
            "Adapter",
            "PASS",
            f"input_tokens={measure.snapshot.input_tokens}, source={measure.snapshot.source}",
        )
    except Exception as e:
        return CheckResult("Measure (synthetic)", "Adapter", "FAIL", str(e))


def _check_decide(adapter_name: str, threshold: int) -> CheckResult:
    """Core: Check if decide logic works."""
    try:
        from context_lantern.core.models import TokenSnapshot, MeasureResult
        from context_lantern.core.decide import make_decision
        from context_lantern.core.state import StateStore
        from pathlib import Path
        import tempfile

        snapshot = TokenSnapshot(input_tokens=threshold + 1, source="test")
        measure = MeasureResult(snapshot=snapshot, dedup_key="doctor-test-key")

        # Use a temp directory to avoid Windows file-lock issues
        tmpdir = tempfile.mkdtemp(prefix="cl_doctor_")
        temp_path = Path(tmpdir) / "test_state.json"
        temp_path.write_text("{}", encoding="utf-8")

        state = StateStore(temp_path)
        decision = make_decision(measure, threshold, state)

        temp_path.unlink(missing_ok=True)
        Path(tmpdir).rmdir()

        return CheckResult(
            "Decide logic",
            "Core",
            "PASS",
            f"decision={decision.decision.value} (input={snapshot.input_tokens} >= threshold={threshold})",
        )
    except Exception as e:
        return CheckResult("Decide logic", "Core", "FAIL", f"{type(e).__name__}: {e}")


def _check_state_rw() -> CheckResult:
    """Core: Check state file read/write."""
    try:
        from context_lantern.core.state import StateStore
        from pathlib import Path
        import tempfile

        tmpdir = tempfile.mkdtemp(prefix="cl_doctor_")
        temp_path = Path(tmpdir) / "test_state.json"
        temp_path.write_text("{}", encoding="utf-8")

        state = StateStore(temp_path)
        state.mark_reminded("test-key", 130000, 120000, "test")
        if not state.is_reminded("test-key", 120000):
            return CheckResult("State read/write", "Core", "FAIL", "is_reminded returned False after mark_reminded")

        # Cleanup
        temp_path.unlink(missing_ok=True)
        Path(tmpdir).rmdir()

        return CheckResult("State read/write", "Core", "PASS", "write + read verified")
    except Exception as e:
        return CheckResult("State read/write", "Core", "FAIL", f"{type(e).__name__}: {e}")


def _check_encode(adapter_name: str) -> CheckResult:
    """Adapter: Check if encode produces valid JSON."""
    try:
        from context_lantern.adapters import get_adapter
        from context_lantern.core.models import (
            Decision,
            ReminderDecision,
            TokenSnapshot,
        )

        adapter = get_adapter(adapter_name)
        decision = ReminderDecision(
            decision=Decision.WARN_ONCE,
            snapshot=TokenSnapshot(input_tokens=125000, source="test"),
            threshold=120000,
            message="test reminder",
        )
        output = adapter.encode(decision)

        if not output:
            return CheckResult("Encode output", "Adapter", "FAIL", "Encoder returned empty string for WARN_ONCE")

        # Verify it's valid JSON
        parsed = json.loads(output)
        return CheckResult(
            "Encode output",
            "Adapter",
            "PASS",
            f"valid JSON with keys: {list(parsed.keys())}",
        )
    except json.JSONDecodeError as e:
        return CheckResult("Encode output", "Adapter", "FAIL", f"Invalid JSON: {e}")
    except Exception as e:
        return CheckResult("Encode output", "Adapter", "FAIL", str(e))


def run_checks(args: argparse.Namespace) -> int:
    """Run all diagnostic checks and print results."""
    adapter_name = args.adapter
    threshold = getattr(args, "threshold", 120_000)

    print(f"Context Lantern Doctor")
    print(f"Adapter: {adapter_name}")
    print(f"Threshold: {threshold}")
    print()

    checks: list[CheckResult] = []

    # Layer 1: Transport
    checks.append(_check_python_version())
    checks.append(_check_stdin_readable())

    # Layer 2: Adapter
    checks.append(_check_adapter_loadable(adapter_name))
    checks.append(_check_measure(adapter_name))

    # Layer 3: Core
    checks.append(_check_decide(adapter_name, threshold))
    checks.append(_check_state_rw())

    # Layer 4: Encode
    checks.append(_check_encode(adapter_name))

    # Print results
    max_name = max(len(c.name) for c in checks)
    max_layer = max(len(c.layer) for c in checks)

    for c in checks:
        icon = {"PASS": "+", "FAIL": "x", "SKIP": "-"}[c.status]
        name_padded = c.name.ljust(max_name)
        layer_padded = f"[{c.layer}]".ljust(max_layer + 2)
        print(f"  {icon} {name_padded} {layer_padded} {c.message}")

    # Summary
    failed = sum(1 for c in checks if c.status == "FAIL")
    passed = sum(1 for c in checks if c.status == "PASS")
    skipped = sum(1 for c in checks if c.status == "SKIP")

    print()
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")

    return 1 if failed > 0 else 0
