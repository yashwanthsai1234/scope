"""Spawn command for scope.

Creates a new scope session with Claude Code running in a tmux session.
"""

import os
from datetime import datetime, timezone

import click

from scope.core.session import Session
from scope.core.state import next_id, save_session
from scope.core.tmux import TmuxError
from scope.core.tmux import create_session as tmux_create_session


@click.command()
@click.argument("task")
def spawn(task: str) -> None:
    """Spawn a new scope session.

    Creates a tmux session running Claude Code with the given task.
    Prints the session ID to stdout.

    TASK is a one-line description of what the session should accomplish.

    Examples:

        scope spawn "Write tests for auth module"

        scope spawn "Refactor database connection handling"
    """
    # Determine parent from environment
    parent = os.environ.get("SCOPE_SESSION_ID", "")

    # Get next available ID
    session_id = next_id(parent)

    # Create session object
    tmux_name = f"scope-{session_id}"
    session = Session(
        id=session_id,
        task=task,
        parent=parent,
        state="running",
        tmux_session=tmux_name,
        created_at=datetime.now(timezone.utc),
    )

    # Save session to filesystem
    save_session(session)

    # Create tmux session with Claude Code
    try:
        tmux_create_session(
            name=tmux_name,
            command="claude",
            env={"SCOPE_SESSION_ID": session_id},
        )
    except TmuxError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)

    # Output session ID
    click.echo(session_id)
