"""Pytest plugin enforcing documentation on collected Python test modules."""

from __future__ import annotations

import ast
import fnmatch
import os
import tokenize
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    import pytest


def _matches_python_files(file_path: Path, config: pytest.Config) -> bool:
    """Return whether *file_path* matches pytest's configured Python patterns."""
    if file_path.suffix != ".py":
        return False

    patterns: list[str] = cast(list[str], config.getini("python_files"))
    return any(_matches_pattern(file_path, pattern) for pattern in patterns)


def _matches_pattern(file_path: Path, pattern: str) -> bool:
    candidate: str = file_path.name
    if os.sep in pattern or (os.altsep is not None and os.altsep in pattern):
        candidate = str(file_path)
        if file_path.is_absolute() and not os.path.isabs(pattern):
            pattern = f"*{os.sep}{pattern}"
    return fnmatch.fnmatch(candidate, pattern)


def _read_module(file_path: Path) -> ast.Module:
    """Parse *file_path* or raise a collection error with source context."""
    try:
        with tokenize.open(file_path) as source_file:
            source: str = source_file.read()
        return ast.parse(source, filename=str(file_path))
    except SyntaxError as error:
        line_number: int = error.lineno or 1
        message: str = (
            f"Malformed Python test module {file_path}:{line_number}: {error.msg}"
        )
        raise _collection_error(message) from error
    except (OSError, UnicodeError) as error:
        raise _collection_error(
            f"Cannot read Python test module {file_path}: {error}"
        ) from error


def _collection_error(message: str) -> Exception:
    from _pytest.nodes import Collector

    return Collector.CollectError(message)


def pytest_collect_file(
    file_path: Path,
    parent: pytest.Collector,
) -> pytest.Collector | None:
    """Reject collected Python test modules without file-level documentation."""
    if not _matches_python_files(file_path, parent.config):
        return None

    module: ast.Module = _read_module(file_path)
    docstring: str | None = ast.get_docstring(module, clean=False)
    if docstring is None or not docstring.strip():
        raise _collection_error(
            f"Python test module requires a file-level docstring: {file_path}"
        )

    return None
