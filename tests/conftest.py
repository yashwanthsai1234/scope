"""Shared pytest fixtures for scope tests."""

import pytest


@pytest.fixture
def mock_scope_base(tmp_path, monkeypatch):
    """Mock get_global_scope_base to return tmp_path for test isolation.

    This ensures tests don't write to the real ~/.scope/ directory.
    We need to mock in multiple places because the function is imported
    directly in some modules.

    Also clears SCOPE_SESSION_ID to prevent parent session pollution.
    """

    def mock_fn():
        return tmp_path

    # Clear session ID to prevent test pollution from parent environment
    monkeypatch.delenv("SCOPE_SESSION_ID", raising=False)

    # Mock in the source module
    monkeypatch.setattr("scope.core.state.get_global_scope_base", mock_fn)

    # Mock in modules that import it directly
    monkeypatch.setattr("scope.hooks.handler.get_global_scope_base", mock_fn)
    monkeypatch.setattr("scope.tui.app.get_global_scope_base", mock_fn)

    return tmp_path
