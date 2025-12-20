"""Top command - launch the scope TUI."""

import os
import uuid

import click


@click.command()
@click.option(
    "--dangerously-skip-permissions",
    is_flag=True,
    envvar="SCOPE_DANGEROUSLY_SKIP_PERMISSIONS",
    help="Pass --dangerously-skip-permissions to spawned Claude instances",
)
def top(dangerously_skip_permissions: bool) -> None:
    """Launch the scope TUI.

    Shows all sessions and auto-refreshes on changes.
    If not running inside tmux, automatically starts tmux first.
    """
    from scope.core.tmux import get_current_session, has_session

    # If not in tmux, exec into tmux running scope top
    if get_current_session() is None:
        if has_session("scope"):
            # Attach to existing scope session
            os.execvp("tmux", ["tmux", "attach-session", "-t", "scope"])
        else:
            # Generate instance ID and build command with env vars
            instance_id = os.environ.get("SCOPE_INSTANCE_ID", "") or str(uuid.uuid4())[:8]
            scope_cmd = f"SCOPE_INSTANCE_ID={instance_id}"
            if dangerously_skip_permissions:
                scope_cmd += " SCOPE_DANGEROUSLY_SKIP_PERMISSIONS=1"
            scope_cmd += " scope top"
            if dangerously_skip_permissions:
                scope_cmd += " --dangerously-skip-permissions"

            os.execvp("tmux", ["tmux", "new-session", "-s", "scope", scope_cmd])

    from scope.tui.app import ScopeApp

    app = ScopeApp(dangerously_skip_permissions=dangerously_skip_permissions)
    app.run()
