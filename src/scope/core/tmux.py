"""tmux wrapper for scope.

Provides functions to create and manage tmux sessions for scope.
"""

import subprocess
from pathlib import Path


class TmuxError(Exception):
    """Raised when a tmux command fails."""

    pass


def create_session(
    name: str,
    command: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> None:
    """Create a new detached tmux session.

    Args:
        name: Session name (e.g., "scope-0")
        command: Command to run in the session
        cwd: Working directory for the session. Defaults to current directory.
        env: Additional environment variables to set.

    Raises:
        TmuxError: If tmux command fails.
    """
    cwd = cwd or Path.cwd()

    # Build command with environment variables
    if env:
        env_prefix = " ".join(f"{k}={v}" for k, v in env.items())
        full_command = f"{env_prefix} {command}"
    else:
        full_command = command

    # tmux new-session -d -s {name} -c {cwd} "{command}"
    cmd = [
        "tmux",
        "new-session",
        "-d",  # Detached
        "-s",
        name,  # Session name
        "-c",
        str(cwd),  # Working directory
        full_command,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise TmuxError(f"Failed to create tmux session: {result.stderr}")


def has_session(name: str) -> bool:
    """Check if a tmux session exists.

    Args:
        name: Session name to check.

    Returns:
        True if session exists, False otherwise.
    """
    result = subprocess.run(
        ["tmux", "has-session", "-t", name],
        capture_output=True,
    )
    return result.returncode == 0
