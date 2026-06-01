"""Tests for core decide logic."""

import tempfile
from pathlib import Path

from context_lantern.core.models import Decision, MeasureResult, TokenSnapshot
from context_lantern.core.decide import make_decision
from context_lantern.core.state import StateStore


def _make_measure(input_tokens: int = 130000, loop_prevention: bool = False) -> MeasureResult:
    return MeasureResult(
        snapshot=TokenSnapshot(input_tokens=input_tokens, source="test"),
        dedup_key="test-dedup-key",
        loop_prevention=loop_prevention,
    )


def _make_state() -> StateStore:
    """Create a state store backed by a temp file."""
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    f.write(b"{}")
    f.close()
    return StateStore(Path(f.name))


def test_below_threshold_is_silent():
    decision = make_decision(_make_measure(input_tokens=50000), 120000, None)
    assert decision.decision == Decision.SILENT


def test_at_threshold_warns():
    decision = make_decision(_make_measure(input_tokens=120000), 120000, None)
    assert decision.decision == Decision.WARN_ONCE


def test_above_threshold_warns():
    decision = make_decision(_make_measure(input_tokens=150000), 120000, None)
    assert decision.decision == Decision.WARN_ONCE


def test_already_reminded_is_silent():
    state = _make_state()
    measure = _make_measure(input_tokens=130000)

    # First call: should warn
    d1 = make_decision(measure, 120000, state)
    assert d1.decision == Decision.WARN_ONCE

    # Second call: same key, should be silent
    d2 = make_decision(measure, 120000, state)
    assert d2.decision == Decision.SILENT
    assert d2.already_reminded is True


def test_loop_prevention_is_silent():
    measure = _make_measure(input_tokens=130000, loop_prevention=True)
    decision = make_decision(measure, 120000, None)
    assert decision.decision == Decision.SILENT


def test_different_dedup_key_can_warn_again():
    state = _make_state()

    m1 = MeasureResult(
        snapshot=TokenSnapshot(input_tokens=130000, source="test"),
        dedup_key="key-1",
    )
    m2 = MeasureResult(
        snapshot=TokenSnapshot(input_tokens=130000, source="test"),
        dedup_key="key-2",  # different key (e.g. forked transcript)
    )

    d1 = make_decision(m1, 120000, state)
    assert d1.decision == Decision.WARN_ONCE

    d2 = make_decision(m2, 120000, state)
    assert d2.decision == Decision.WARN_ONCE  # different key, warns again


def test_old_low_threshold_does_not_block():
    """State recorded with a lower threshold shouldn't block a higher threshold."""
    state = _make_state()
    # Simulate a previous reminder at a low test threshold
    state.mark_reminded("test-key", 50000, 50000, "test")

    measure = MeasureResult(
        snapshot=TokenSnapshot(input_tokens=130000, source="test"),
        dedup_key="test-key",
    )
    # At the real threshold (120000), the old entry (50000 < 120000) shouldn't block
    decision = make_decision(measure, 120000, state)
    assert decision.decision == Decision.WARN_ONCE


def test_no_state_always_warns():
    """With state=None, should always warn above threshold."""
    d1 = make_decision(_make_measure(130000), 120000, None)
    d2 = make_decision(_make_measure(130000), 120000, None)
    assert d1.decision == Decision.WARN_ONCE
    assert d2.decision == Decision.WARN_ONCE
