"""Wait command for scope.

Blocks until session(s) complete (done or aborted).
"""

from pathlib import Path

import click
from watchfiles import watch

from scope.core.state import load_session


TERMINAL_STATES = {"done", "aborted"}


@click.command()
@click.argument("session_ids", nargs=-1, required=True)
def wait(session_ids: tuple[str, ...]) -> None:
    """Wait for session(s) to complete.

    Blocks until all sessions reach 'done' or 'aborted' state.
    Outputs result file content (if any). Exit code indicates status:
    0 = all done, 1 = error, 2 = any aborted.

    SESSION_IDS are the IDs of sessions to wait for.

    Examples:

        scope wait 0

        scope wait 0 1 2
    """
    # Validate all sessions exist
    pending: dict[str, Path] = {}  # session_id -> session_dir
    for session_id in session_ids:
        session = load_session(session_id)
        if session is None:
            click.echo(f"Session {session_id} not found", err=True)
            raise SystemExit(1)
        pending[session_id] = Path.cwd() / ".scope" / "sessions" / session_id

    results: dict[str, str] = {}  # session_id -> state

    # Check for already-completed sessions
    for session_id in list(pending.keys()):
        session = load_session(session_id)
        if session and session.state in TERMINAL_STATES:
            results[session_id] = session.state
            del pending[session_id]

    # If all already done, output and exit
    if not pending:
        _output_results(session_ids, results)
        return

    # Watch all pending session directories
    watch_paths = list(pending.values())

    for changes in watch(*watch_paths):
        for _, path in changes:
            path = Path(path)
            # Check if this is a state file change
            if path.name == "state":
                session_id = path.parent.name
                if session_id in pending:
                    session = load_session(session_id)
                    if session is None:
                        click.echo(f"Session {session_id} was deleted", err=True)
                        raise SystemExit(1)
                    if session.state in TERMINAL_STATES:
                        results[session_id] = session.state
                        del pending[session_id]

        # All done?
        if not pending:
            _output_results(session_ids, results)
            return


def _output_results(session_ids: tuple[str, ...], states: dict[str, str]) -> None:
    """Output results for all sessions and exit with appropriate code."""
    any_aborted = False
    multiple = len(session_ids) > 1

    for session_id in session_ids:
        result_file = Path.cwd() / ".scope" / "sessions" / session_id / "result"
        if result_file.exists():
            if multiple:
                click.echo(f"[{session_id}]")
            click.echo(result_file.read_text(), nl=False)
            if multiple:
                click.echo("\n")

        if states.get(session_id) == "aborted":
            any_aborted = True

    if any_aborted:
        raise SystemExit(2)
