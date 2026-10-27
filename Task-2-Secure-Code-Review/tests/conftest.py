"""Shared pytest fixtures."""
from __future__ import annotations

import pytest

import app.main as main


@pytest.fixture(autouse=True)
def isolated_application_state(monkeypatch, tmp_path):
    """Keep tests away from the repository database and host API key."""
    monkeypatch.setattr(main, "DB_PATH", tmp_path / "test.sqlite3")
    monkeypatch.setattr(main, "API_KEY", "")
    yield
