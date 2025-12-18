"""Tests for tmux wrapper.

Note: These tests require tmux to be installed.
"""

import subprocess

import pytest

from scope.core.tmux import TmuxError, create_session, has_session


def tmux_available() -> bool:
    """Check if tmux is available."""
    result = subprocess.run(["which", "tmux"], capture_output=True)
    return result.returncode == 0


@pytest.fixture
def cleanup_session():
    """Fixture to cleanup tmux sessions after tests."""
    sessions = []
    yield sessions
    for name in sessions:
        subprocess.run(["tmux", "kill-session", "-t", name], capture_output=True)


@pytest.mark.skipif(not tmux_available(), reason="tmux not installed")
def test_create_session(cleanup_session, tmp_path):
    """Test creating a tmux session."""
    name = "scope-test-create"
    cleanup_session.append(name)

    create_session(name=name, command="sleep 60", cwd=tmp_path)

    assert has_session(name)


@pytest.mark.skipif(not tmux_available(), reason="tmux not installed")
def test_create_session_with_env(cleanup_session, tmp_path):
    """Test creating a session with environment variables."""
    name = "scope-test-env"
    cleanup_session.append(name)

    create_session(
        name=name,
        command="sleep 60",
        cwd=tmp_path,
        env={"SCOPE_SESSION_ID": "0"},
    )

    assert has_session(name)


@pytest.mark.skipif(not tmux_available(), reason="tmux not installed")
def test_has_session_false():
    """Test has_session returns False for non-existent session."""
    assert not has_session("nonexistent-session-12345")


@pytest.mark.skipif(not tmux_available(), reason="tmux not installed")
def test_create_session_duplicate_fails(cleanup_session, tmp_path):
    """Test creating duplicate session raises error."""
    name = "scope-test-dup"
    cleanup_session.append(name)

    create_session(name=name, command="sleep 60", cwd=tmp_path)

    with pytest.raises(TmuxError):
        create_session(name=name, command="sleep 60", cwd=tmp_path)
