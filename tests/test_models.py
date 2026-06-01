"""Tests for core data models."""

from context_lantern.core.models import (
    Decision,
    MeasureResult,
    ReminderDecision,
    TokenSnapshot,
)


def test_token_snapshot_defaults():
    s = TokenSnapshot(input_tokens=50000)
    assert s.input_tokens == 50000
    assert s.cached_input_tokens == 0
    assert s.total_tokens == 0
    assert s.model_context_window == 0
    assert s.source == "unknown"


def test_token_snapshot_frozen():
    s = TokenSnapshot(input_tokens=50000)
    try:
        s.input_tokens = 60000  # type: ignore
        assert False, "Should have raised"
    except AttributeError:
        pass


def test_measure_result():
    snapshot = TokenSnapshot(input_tokens=100000, source="transcript")
    m = MeasureResult(snapshot=snapshot, dedup_key="abc-123")
    assert m.dedup_key == "abc-123"
    assert m.loop_prevention is False
    assert m.meta == {}


def test_decision_enum():
    assert Decision.SILENT.value == "silent"
    assert Decision.WARN_ONCE.value == "warn_once"


def test_reminder_decision():
    snapshot = TokenSnapshot(input_tokens=130000, source="payload")
    d = ReminderDecision(
        decision=Decision.WARN_ONCE,
        snapshot=snapshot,
        threshold=120000,
        message="test",
    )
    assert d.decision == Decision.WARN_ONCE
    assert d.already_reminded is False
