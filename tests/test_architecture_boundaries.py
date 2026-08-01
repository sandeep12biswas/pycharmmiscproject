"""Enforces the architectural boundaries documented in PROGRESS.md as design
decisions, and the offline/no-network requirement (NFR-4), by statically
scanning imports rather than relying on manual review staying accurate."""

import ast
from pathlib import Path
from typing import Set

import pytest

APP_DIR = Path(__file__).resolve().parent.parent / "app"

NETWORK_MODULES = {
    "socket",
    "urllib",
    "http",
    "requests",
    "httpx",
    "aiohttp",
    "ftplib",
    "smtplib",
    "telnetlib",
    "xmlrpc",
}


def _imported_top_level_modules(py_file: Path) -> Set[str]:
    tree = ast.parse(py_file.read_text(), filename=str(py_file))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def _imported_dotted_names(py_file: Path) -> Set[str]:
    """Full dotted import paths (e.g. 'PySide6.QtNetwork'), for checks that
    care about a specific submodule rather than just the top-level package."""
    tree = ast.parse(py_file.read_text(), filename=str(py_file))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _all_py_files(directory: Path):
    return sorted(directory.rglob("*.py")) if directory.is_dir() else []


@pytest.mark.parametrize("py_file", _all_py_files(APP_DIR / "repositories"), ids=lambda p: p.name)
def test_repositories_never_import_pyside6(py_file):
    assert "PySide6" not in _imported_top_level_modules(py_file)


@pytest.mark.parametrize("py_file", _all_py_files(APP_DIR / "models"), ids=lambda p: p.name)
def test_models_never_import_pyside6(py_file):
    assert "PySide6" not in _imported_top_level_modules(py_file)


@pytest.mark.parametrize("py_file", _all_py_files(APP_DIR / "ui"), ids=lambda p: p.name)
def test_ui_widgets_never_import_sqlite3_directly(py_file):
    assert "sqlite3" not in _imported_top_level_modules(py_file)


@pytest.mark.parametrize("py_file", _all_py_files(APP_DIR / "controllers"), ids=lambda p: p.name)
def test_controllers_never_import_sqlite3_directly(py_file):
    assert "sqlite3" not in _imported_top_level_modules(py_file)


@pytest.mark.parametrize("py_file", _all_py_files(APP_DIR), ids=lambda p: str(p.relative_to(APP_DIR)))
def test_no_network_modules_imported_anywhere(py_file):
    used = _imported_top_level_modules(py_file) & NETWORK_MODULES
    assert not used, f"{py_file} imports network module(s): {used}"


@pytest.mark.parametrize("py_file", _all_py_files(APP_DIR), ids=lambda p: str(p.relative_to(APP_DIR)))
def test_qtnetwork_never_used(py_file):
    dotted = _imported_dotted_names(py_file)
    assert not any(name.startswith("PySide6.QtNetwork") for name in dotted)
