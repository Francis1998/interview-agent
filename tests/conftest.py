"""Shared pytest fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def knowledge_dir(tmp_path: Path) -> Path:
    """Provide minimal knowledge base for tests."""
    content = "# Python\n\n##### GIL\nGlobal Interpreter Lock in CPython.\n"
    path = tmp_path / "python.md"
    path.write_text(content, encoding="utf-8")
    return tmp_path
