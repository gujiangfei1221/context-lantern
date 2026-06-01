"""Tests for Codex adapter (integration-level)."""

import argparse
import json
import tempfile
from pathlib import Path

from context_lantern.core.models import Decision


def _make_transcript(tmpdir: Path, input_tokens: int = 130000) -> Path:
    """Create a minimal Codex-style transcript JSONL."""
    transcript = tmpdir / "rollout-gpt4-26-01T12-00-00-abc123def.jsonl"
    entry = {
        "payload": {
            "type": "token_count",
            "info": {
                "last_token_usage": {
                    "input_tokens": input_tokens,
                    "cached_input_tokens": 0,
                    "total_tokens": input_tokens + 500,
                },
                "model_context_window": 200000,
            },
        }
    }
    transcript.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    return transcript


def test_codex_measure_parses_transcript():
    from context_lantern.adapters.codex_stop import CodexStopAdapter

    adapter = CodexStopAdapter()
    with tempfile.TemporaryDirectory() as tmpdir:
        transcript = _make_transcript(Path(tmpdir), input_tokens=130000)
        args = argparse.Namespace(transcript_path=str(transcript))
        result = adapter.measure({}, args)

    assert result is not None
    assert result.snapshot.input_tokens == 130000
    assert result.snapshot.source == "transcript"
    assert result.dedup_key == "abc123def"


def test_codex_measure_loop_prevention():
    from context_lantern.adapters.codex_stop import CodexStopAdapter

    adapter = CodexStopAdapter()
    with tempfile.TemporaryDirectory() as tmpdir:
        transcript = _make_transcript(Path(tmpdir))
        args = argparse.Namespace(transcript_path=str(transcript))
        result = adapter.measure({"stop_hook_active": True}, args)

    assert result is not None
    assert result.loop_prevention is True


def test_codex_encode_warn():
    from context_lantern.adapters.codex_stop import CodexStopAdapter
    from context_lantern.core.models import ReminderDecision, TokenSnapshot

    adapter = CodexStopAdapter()
    decision = ReminderDecision(
        decision=Decision.WARN_ONCE,
        snapshot=TokenSnapshot(input_tokens=130000, source="transcript"),
        threshold=120000,
        message="test",
    )
    output = adapter.encode(decision)
    parsed = json.loads(output)

    assert parsed["decision"] == "block"
    assert "session-handoff" in parsed["reason"]


def test_codex_encode_silent():
    from context_lantern.adapters.codex_stop import CodexStopAdapter
    from context_lantern.core.models import ReminderDecision, TokenSnapshot

    adapter = CodexStopAdapter()
    decision = ReminderDecision(
        decision=Decision.SILENT,
        snapshot=TokenSnapshot(input_tokens=50000, source="transcript"),
        threshold=120000,
    )
    output = adapter.encode(decision)
    assert output == ""


def test_codex_end_to_end():
    """Full pipeline: measure -> decide -> encode for Codex."""
    from context_lantern.adapters.codex_stop import CodexStopAdapter
    from context_lantern.core.decide import make_decision
    from context_lantern.core.state import StateStore

    adapter = CodexStopAdapter()

    with tempfile.TemporaryDirectory() as tmpdir:
        transcript = _make_transcript(Path(tmpdir), input_tokens=130000)
        args = argparse.Namespace(transcript_path=str(transcript))
        measure = adapter.measure({}, args)
        assert measure is not None

        state_file = Path(tmpdir) / "state.json"
        state_file.write_text("{}", encoding="utf-8")
        state = StateStore(state_file)

        # First call: should warn
        decision = make_decision(measure, 120000, state)
        assert decision.decision == Decision.WARN_ONCE

        output = adapter.encode(decision)
        parsed = json.loads(output)
        assert parsed["decision"] == "block"

        # Second call: should be silent (same dedup key)
        decision2 = make_decision(measure, 120000, state)
        assert decision2.decision == Decision.SILENT
