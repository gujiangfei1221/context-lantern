"""Tests for state management."""

import tempfile
from pathlib import Path

from context_lantern.core.state import StateStore


def _make_state() -> StateStore:
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    f.write(b"{}")
    f.close()
    return StateStore(Path(f.name))


def test_empty_state():
    state = _make_state()
    assert state.is_reminded("nonexistent", 120000) is False


def test_mark_and_check():
    state = _make_state()
    state.mark_reminded("key-1", 130000, 120000, "transcript")
    assert state.is_reminded("key-1", 120000) is True


def test_low_token_does_not_satisfy_high_threshold():
    state = _make_state()
    state.mark_reminded("key-1", 50000, 50000, "test")
    # 50000 < 120000, so not considered "reminded" at the higher threshold
    assert state.is_reminded("key-1", 120000) is False


def test_persistence():
    """State should survive reload."""
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    f.write(b"{}")
    f.close()
    path = Path(f.name)

    state1 = StateStore(path)
    state1.mark_reminded("key-1", 130000, 120000, "transcript")

    # Reload from same file
    state2 = StateStore(path)
    assert state2.is_reminded("key-1", 120000) is True


def test_all_entries():
    state = _make_state()
    state.mark_reminded("k1", 100000, 80000)
    state.mark_reminded("k2", 200000, 120000)
    entries = state.all_entries()
    assert len(entries) == 2
    assert "k1" in entries
    assert "k2" in entries


def test_corrupted_state_file():
    """Should handle corrupted state file gracefully."""
    f = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    f.write(b"not json at all!!!")
    f.close()
    state = StateStore(Path(f.name))
    assert state.is_reminded("any-key", 120000) is False
