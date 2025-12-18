"""Tests for state management."""

from datetime import datetime, timezone

from scope.core.session import Session
from scope.core.state import ensure_scope_dir, next_id, save_session


def test_ensure_scope_dir(tmp_path, monkeypatch):
    """Test ensure_scope_dir creates directory structure."""
    monkeypatch.chdir(tmp_path)

    scope_dir = ensure_scope_dir()

    assert scope_dir.exists()
    assert (scope_dir / "sessions").exists()
    assert scope_dir == tmp_path / ".scope"


def test_ensure_scope_dir_idempotent(tmp_path, monkeypatch):
    """Test ensure_scope_dir can be called multiple times."""
    monkeypatch.chdir(tmp_path)

    scope_dir1 = ensure_scope_dir()
    scope_dir2 = ensure_scope_dir()

    assert scope_dir1 == scope_dir2
    assert scope_dir1.exists()


def test_next_id_root_sessions(tmp_path, monkeypatch):
    """Test next_id generates sequential root IDs."""
    monkeypatch.chdir(tmp_path)

    assert next_id() == "0"
    assert next_id() == "1"
    assert next_id() == "2"


def test_next_id_persists(tmp_path, monkeypatch):
    """Test next_id counter is persisted to disk."""
    monkeypatch.chdir(tmp_path)

    next_id()  # "0"
    next_id()  # "1"

    # Verify counter file
    counter_file = tmp_path / ".scope" / "next_id"
    assert counter_file.exists()
    assert counter_file.read_text().strip() == "2"


def test_next_id_child_sessions(tmp_path, monkeypatch):
    """Test next_id generates child IDs under parent."""
    monkeypatch.chdir(tmp_path)

    # Create parent session directory
    scope_dir = ensure_scope_dir()
    (scope_dir / "sessions" / "0").mkdir(parents=True)

    assert next_id("0") == "0.0"

    # Create child directory to simulate existing child
    (scope_dir / "sessions" / "0.0").mkdir()
    assert next_id("0") == "0.1"


def test_next_id_nested_children(tmp_path, monkeypatch):
    """Test next_id handles deeply nested children."""
    monkeypatch.chdir(tmp_path)

    scope_dir = ensure_scope_dir()
    (scope_dir / "sessions" / "0").mkdir(parents=True)
    (scope_dir / "sessions" / "0.0").mkdir()

    # Child of 0.0 should be 0.0.0
    assert next_id("0.0") == "0.0.0"


def test_save_session(tmp_path, monkeypatch):
    """Test save_session writes all files correctly."""
    monkeypatch.chdir(tmp_path)

    created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    session = Session(
        id="0",
        task="Test task",
        parent="",
        state="running",
        tmux_session="scope-0",
        created_at=created,
    )

    save_session(session)

    session_dir = tmp_path / ".scope" / "sessions" / "0"
    assert session_dir.exists()
    assert (session_dir / "task").read_text() == "Test task"
    assert (session_dir / "state").read_text() == "running"
    assert (session_dir / "parent").read_text() == ""
    assert (session_dir / "tmux").read_text() == "scope-0"
    assert (session_dir / "created_at").read_text() == created.isoformat()


def test_save_session_with_parent(tmp_path, monkeypatch):
    """Test save_session with parent ID."""
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

    session_dir = tmp_path / ".scope" / "sessions" / "0.1"
    assert (session_dir / "parent").read_text() == "0"
