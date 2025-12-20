"""Tests for wait command."""

import threading
import time
from datetime import datetime, timezone

import pytest
from click.testing import CliRunner

from scope.cli import main
from scope.core.session import Session
from scope.core.state import save_session, update_state


@pytest.fixture
def runner():
    """Click CLI test runner."""
    return CliRunner()


def test_wait_help(runner):
    """Test wait --help shows usage."""
    result = runner.invoke(main, ["wait", "--help"])
    assert result.exit_code == 0
    assert "Wait for session(s) to complete" in result.output


def test_wait_no_args(runner):
    """Test wait without session_id shows error."""
    result = runner.invoke(main, ["wait"])
    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_wait_session_not_found(runner, tmp_path, monkeypatch):
    """Test wait with non-existent session returns error."""
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(main, ["wait", "999"])

    assert result.exit_code == 1
    assert "Session 999 not found" in result.output


def test_wait_already_done(runner, tmp_path, monkeypatch):
    """Test wait returns immediately if session already done."""
    monkeypatch.chdir(tmp_path)

    session = Session(
        id="0",
        task="Test task",
        parent="",
        state="done",
        tmux_session="scope-0",
        created_at=datetime.now(timezone.utc),
    )
    save_session(session)

    result = runner.invoke(main, ["wait", "0"])

    assert result.exit_code == 0
    assert result.output == ""  # No result file


def test_wait_already_aborted(runner, tmp_path, monkeypatch):
    """Test wait returns immediately if session already aborted."""
    monkeypatch.chdir(tmp_path)

    session = Session(
        id="0",
        task="Test task",
        parent="",
        state="aborted",
        tmux_session="scope-0",
        created_at=datetime.now(timezone.utc),
    )
    save_session(session)

    result = runner.invoke(main, ["wait", "0"])

    assert result.exit_code == 2  # Aborted exit code


def test_wait_with_result(runner, tmp_path, monkeypatch):
    """Test wait outputs result file content."""
    monkeypatch.chdir(tmp_path)

    session = Session(
        id="0",
        task="Test task",
        parent="",
        state="done",
        tmux_session="scope-0",
        created_at=datetime.now(timezone.utc),
    )
    save_session(session)

    # Write result file
    result_file = tmp_path / ".scope" / "sessions" / "0" / "result"
    result_file.write_text("Task completed successfully.")

    result = runner.invoke(main, ["wait", "0"])

    assert result.exit_code == 0
    assert result.output == "Task completed successfully."


def test_wait_blocks_until_done(runner, tmp_path, monkeypatch):
    """Test wait blocks until session state changes to done."""
    monkeypatch.chdir(tmp_path)

    session = Session(
        id="0",
        task="Test task",
        parent="",
        state="running",
        tmux_session="scope-0",
        created_at=datetime.now(timezone.utc),
    )
    save_session(session)

    # Complete the session in a background thread after a delay
    def complete_session():
        time.sleep(0.3)
        update_state("0", "done")

    thread = threading.Thread(target=complete_session)
    thread.start()

    result = runner.invoke(main, ["wait", "0"])

    thread.join()

    assert result.exit_code == 0


def test_wait_child_session(runner, tmp_path, monkeypatch):
    """Test wait works with child session IDs."""
    monkeypatch.chdir(tmp_path)

    session = Session(
        id="0.1",
        task="Child task",
        parent="0",
        state="done",
        tmux_session="scope-0.1",
        created_at=datetime.now(timezone.utc),
    )
    save_session(session)

    result = runner.invoke(main, ["wait", "0.1"])

    assert result.exit_code == 0


def test_wait_multiple_sessions(runner, tmp_path, monkeypatch):
    """Test wait works with multiple session IDs."""
    monkeypatch.chdir(tmp_path)

    for i in range(3):
        session = Session(
            id=str(i),
            task=f"Task {i}",
            parent="",
            state="done",
            tmux_session=f"scope-{i}",
            created_at=datetime.now(timezone.utc),
        )
        save_session(session)
        result_file = tmp_path / ".scope" / "sessions" / str(i) / "result"
        result_file.write_text(f"Result {i}")

    result = runner.invoke(main, ["wait", "0", "1", "2"])

    assert result.exit_code == 0
    assert "[0]" in result.output
    assert "Result 0" in result.output
    assert "[1]" in result.output
    assert "Result 1" in result.output
    assert "[2]" in result.output
    assert "Result 2" in result.output


def test_wait_multiple_one_aborted(runner, tmp_path, monkeypatch):
    """Test wait exits 2 if any session aborted."""
    monkeypatch.chdir(tmp_path)

    session0 = Session(
        id="0",
        task="Task 0",
        parent="",
        state="done",
        tmux_session="scope-0",
        created_at=datetime.now(timezone.utc),
    )
    save_session(session0)

    session1 = Session(
        id="1",
        task="Task 1",
        parent="",
        state="aborted",
        tmux_session="scope-1",
        created_at=datetime.now(timezone.utc),
    )
    save_session(session1)

    result = runner.invoke(main, ["wait", "0", "1"])

    assert result.exit_code == 2


def test_wait_multiple_blocks_until_all_done(runner, tmp_path, monkeypatch):
    """Test wait blocks until all sessions complete."""
    monkeypatch.chdir(tmp_path)

    # Create two running sessions
    for i in range(2):
        session = Session(
            id=str(i),
            task=f"Task {i}",
            parent="",
            state="running",
            tmux_session=f"scope-{i}",
            created_at=datetime.now(timezone.utc),
        )
        save_session(session)

    # Complete sessions in background threads
    def complete_session(sid, delay):
        time.sleep(delay)
        update_state(sid, "done")

    threads = [
        threading.Thread(target=complete_session, args=("0", 0.2)),
        threading.Thread(target=complete_session, args=("1", 0.4)),
    ]
    for t in threads:
        t.start()

    result = runner.invoke(main, ["wait", "0", "1"])

    for t in threads:
        t.join()

    assert result.exit_code == 0
