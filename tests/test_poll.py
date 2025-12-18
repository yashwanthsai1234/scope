"""Tests for poll command."""

from datetime import datetime, timezone

import orjson
import pytest
from click.testing import CliRunner

from scope.cli import main
from scope.core.session import Session
from scope.core.state import save_session


@pytest.fixture
def runner():
    """Click CLI test runner."""
    return CliRunner()


def test_poll_help(runner):
    """Test poll --help shows usage."""
    result = runner.invoke(main, ["poll", "--help"])
    assert result.exit_code == 0
    assert "Poll a session's status" in result.output


def test_poll_no_args(runner):
    """Test poll without session_id shows error."""
    result = runner.invoke(main, ["poll"])
    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_poll_session_not_found(runner, tmp_path, monkeypatch):
    """Test poll with non-existent session returns error."""
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(main, ["poll", "999"])

    assert result.exit_code == 1
    assert "Session 999 not found" in result.output


def test_poll_running_session(runner, tmp_path, monkeypatch):
    """Test poll returns status for running session."""
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

    result = runner.invoke(main, ["poll", "0"])

    assert result.exit_code == 0
    data = orjson.loads(result.output)
    assert data["status"] == "running"


def test_poll_done_session(runner, tmp_path, monkeypatch):
    """Test poll returns status for completed session."""
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

    result = runner.invoke(main, ["poll", "0"])

    assert result.exit_code == 0
    data = orjson.loads(result.output)
    assert data["status"] == "done"


def test_poll_with_activity(runner, tmp_path, monkeypatch):
    """Test poll returns activity when present."""
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

    # Write activity file
    activity_file = tmp_path / ".scope" / "sessions" / "0" / "activity"
    activity_file.write_text("editing src/auth.ts")

    result = runner.invoke(main, ["poll", "0"])

    assert result.exit_code == 0
    data = orjson.loads(result.output)
    assert data["status"] == "running"
    assert data["activity"] == "editing src/auth.ts"


def test_poll_with_result(runner, tmp_path, monkeypatch):
    """Test poll returns result when session is done."""
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
    result_file.write_text("Completed successfully. Updated 3 files.")

    result = runner.invoke(main, ["poll", "0"])

    assert result.exit_code == 0
    data = orjson.loads(result.output)
    assert data["status"] == "done"
    assert data["result"] == "Completed successfully. Updated 3 files."


def test_poll_child_session(runner, tmp_path, monkeypatch):
    """Test poll works with child session IDs."""
    monkeypatch.chdir(tmp_path)

    session = Session(
        id="0.1",
        task="Child task",
        parent="0",
        state="running",
        tmux_session="scope-0.1",
        created_at=datetime.now(timezone.utc),
    )
    save_session(session)

    result = runner.invoke(main, ["poll", "0.1"])

    assert result.exit_code == 0
    data = orjson.loads(result.output)
    assert data["status"] == "running"
