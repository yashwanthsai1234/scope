"""Tests for spawn command."""

import subprocess

import pytest
from click.testing import CliRunner

from scope.cli import main


def tmux_available() -> bool:
    """Check if tmux is available."""
    result = subprocess.run(["which", "tmux"], capture_output=True)
    return result.returncode == 0


def session_exists(session_name: str) -> bool:
    """Check if a tmux session exists."""
    result = subprocess.run(
        ["tmux", "has-session", "-t", session_name],
        capture_output=True,
    )
    return result.returncode == 0


@pytest.fixture
def cleanup_scope_sessions():
    """Fixture to cleanup scope tmux sessions before and after tests."""
    # Clean before test to ensure fresh state
    for i in range(10):
        subprocess.run(["tmux", "kill-session", "-t", f"scope-{i}"], capture_output=True)
        subprocess.run(["tmux", "kill-session", "-t", f"scope-0.{i}"], capture_output=True)
    yield
    # Clean after test
    for i in range(10):
        subprocess.run(["tmux", "kill-session", "-t", f"scope-{i}"], capture_output=True)
        subprocess.run(["tmux", "kill-session", "-t", f"scope-0.{i}"], capture_output=True)


@pytest.fixture
def runner():
    """Click CLI test runner."""
    return CliRunner()


def test_spawn_no_args(runner):
    """Test spawn without task argument shows error."""
    result = runner.invoke(main, ["spawn"])
    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_spawn_help(runner):
    """Test spawn --help shows usage."""
    result = runner.invoke(main, ["spawn", "--help"])
    assert result.exit_code == 0
    assert "Spawn a new scope session" in result.output


@pytest.mark.skipif(not tmux_available(), reason="tmux not installed")
def test_spawn_creates_session(runner, tmp_path, monkeypatch, cleanup_scope_sessions):
    """Test spawn creates session files and tmux session."""
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(main, ["spawn", "Test task"])

    assert result.exit_code == 0
    session_id = result.output.strip()
    assert session_id == "0"

    # Verify filesystem
    session_dir = tmp_path / ".scope" / "sessions" / "0"
    assert session_dir.exists()
    assert (session_dir / "task").read_text() == "Test task"
    assert (session_dir / "state").read_text() == "running"

    # Verify tmux session exists (independent session, not window)
    tmux_session = f"scope-{session_id}"
    assert session_exists(tmux_session)


@pytest.mark.skipif(not tmux_available(), reason="tmux not installed")
def test_spawn_sequential_ids(runner, tmp_path, monkeypatch, cleanup_scope_sessions):
    """Test multiple spawns get sequential IDs."""
    monkeypatch.chdir(tmp_path)

    result1 = runner.invoke(main, ["spawn", "Task 1"])
    result2 = runner.invoke(main, ["spawn", "Task 2"])

    assert result1.output.strip() == "0"
    assert result2.output.strip() == "1"


@pytest.mark.skipif(not tmux_available(), reason="tmux not installed")
def test_spawn_with_parent(runner, tmp_path, monkeypatch, cleanup_scope_sessions):
    """Test spawn with SCOPE_SESSION_ID creates child session."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SCOPE_SESSION_ID", "0")

    # Create parent directory first
    (tmp_path / ".scope" / "sessions" / "0").mkdir(parents=True)

    result = runner.invoke(main, ["spawn", "Child task"])

    assert result.exit_code == 0
    session_id = result.output.strip()
    assert session_id == "0.0"

    # Verify parent is set correctly
    session_dir = tmp_path / ".scope" / "sessions" / "0.0"
    assert (session_dir / "parent").read_text() == "0"
