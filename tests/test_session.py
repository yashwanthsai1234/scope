"""Tests for session dataclass."""

from datetime import datetime, timezone

import pytest

from scope.core.session import Session


def test_session_creation():
    """Test creating a valid session."""
    session = Session(
        id="0",
        task="Test task",
        parent="",
        state="running",
        tmux_session="scope-0",
        created_at=datetime.now(timezone.utc),
    )
    assert session.id == "0"
    assert session.task == "Test task"
    assert session.parent == ""
    assert session.state == "running"
    assert session.tmux_session == "scope-0"


def test_session_invalid_state():
    """Test that invalid state raises ValueError."""
    with pytest.raises(ValueError, match="Invalid state"):
        Session(
            id="0",
            task="Test",
            parent="",
            state="invalid",
            tmux_session="scope-0",
            created_at=datetime.now(timezone.utc),
        )


def test_session_all_valid_states():
    """Test all valid states are accepted."""
    for state in ["pending", "running", "done", "aborted"]:
        session = Session(
            id="0",
            task="Test",
            parent="",
            state=state,
            tmux_session="scope-0",
            created_at=datetime.now(timezone.utc),
        )
        assert session.state == state


def test_session_child_id():
    """Test session with child ID format."""
    session = Session(
        id="0.1.2",
        task="Nested task",
        parent="0.1",
        state="pending",
        tmux_session="scope-0.1.2",
        created_at=datetime.now(timezone.utc),
    )
    assert session.id == "0.1.2"
    assert session.parent == "0.1"
