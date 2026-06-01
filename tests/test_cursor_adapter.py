"""Tests for Cursor adapter (integration-level)."""

import argparse
import json
import tempfile
from pathlib import Path

from context_lantern.core.models import Decision


def test_cursor_measure_from_payload():
    from context_lantern.adapters.cursor_stop import CursorStopAdapter

    adapter = CursorStopAdapter()
    payload = {
        "input_tokens": 130000,
        "cache_read_tokens": 20000,
        "total_tokens": 135000,
        "conversation_id": "conv-abc-123",
    }
    args = argparse.Namespace(transcript_path=None, cursor_home=Path("/nonexistent"))
    result = adapter.measure(payload, args)

    assert result is not None
    # effective_input = 130000 - 20000 = 110000
    assert result.snapshot.input_tokens == 110000
    assert result.snapshot.cached_input_tokens == 20000
    assert result.snapshot.source == "payload_cache"
    assert result.dedup_key == "conv-abc-123"


def test_cursor_measure_loop_prevention():
    from context_lantern.adapters.cursor_stop import CursorStopAdapter

    adapter = CursorStopAdapter()
    payload = {
        "input_tokens": 130000,
        "conversation_id": "conv-1",
        "loop_count": 2,
    }
    args = argparse.Namespace(transcript_path=None, cursor_home=Path("/nonexistent"))
    result = adapter.measure(payload, args)

    assert result is not None
    assert result.loop_prevention is True


def test_cursor_encode_warn():
    from context_lantern.adapters.cursor_stop import CursorStopAdapter
    from context_lantern.core.models import ReminderDecision, TokenSnapshot

    adapter = CursorStopAdapter()
    decision = ReminderDecision(
        decision=Decision.WARN_ONCE,
        snapshot=TokenSnapshot(input_tokens=130000, source="payload_cache"),
        threshold=120000,
        message="test",
    )
    output = adapter.encode(decision)
    parsed = json.loads(output)

    assert "followup_message" in parsed
    assert "130k" in parsed["followup_message"]


def test_cursor_encode_silent():
    from context_lantern.adapters.cursor_stop import CursorStopAdapter
    from context_lantern.core.models import ReminderDecision, TokenSnapshot

    adapter = CursorStopAdapter()
    decision = ReminderDecision(
        decision=Decision.SILENT,
        snapshot=TokenSnapshot(input_tokens=50000, source="payload"),
        threshold=120000,
    )
    output = adapter.encode(decision)
    assert output == ""
