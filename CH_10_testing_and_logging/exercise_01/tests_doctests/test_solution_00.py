"""Tests for recursive module doctest discovery."""

from __future__ import annotations

import doctest
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

from CH_10_testing_and_logging.exercise_01 import solution_00
from CH_10_testing_and_logging.exercise_01.tests_doctests import fixture_module


def test_module_runner_aggregates_module_function_class_and_method_examples() -> None:
    result: doctest.TestResults = solution_00.run_module_doctests(fixture_module)

    assert result == doctest.TestResults(failed=0, attempted=4)


def test_module_runner_rejects_non_module_targets() -> None:
    with pytest.raises(TypeError, match="target must be a module"):
        solution_00.run_module_doctests(cast(ModuleType, object()))


def test_public_doctest_entry_point_imports_without_third_party_packages() -> None:
    repository_root: Path = Path(__file__).parents[3]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            (
                "from CH_10_testing_and_logging.exercise_01.solution_00 "
                "import run_doctests"
            ),
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
