"""Tests for the recursive doctest runner."""

from __future__ import annotations

import doctest
import inspect
import subprocess
import sys
from pathlib import Path
from typing import get_type_hints

import pytest

from CH_10_testing_and_logging.exercise_01.solution_00 import (
    main,
    run_doctests,
)

_OFFSET: int = 7


def _passing_example() -> None:
    """
    >>> sorted([3, 1, 2])
    [1, 2, 3]
    """


def _failing_example() -> None:
    """
    >>> 2 + 2
    5
    """


def _no_examples() -> None:
    """Contain no doctest examples."""


def _ellipsis_example() -> None:
    """
    >>> print("prefix: variable suffix")
    prefix: ... suffix
    """


def _uses_module_global(value: int) -> int:
    """
    >>> _uses_module_global(5)
    12
    """
    return value + _OFFSET


class _Calculator:
    """
    Create a calculator.

    >>> calculator = _Calculator(4)
    >>> calculator.double()
    8
    """

    def __init__(self, value: int) -> None:
        self.value: int = value

    def double(self) -> int:
        """
        Return twice the configured value.

        >>> _Calculator(3).double()
        6
        """
        return self.value * 2


def test_passing_doctest_returns_exact_test_results_type() -> None:
    result: doctest.TestResults = run_doctests(_passing_example)

    assert type(result) is doctest.TestResults
    assert result == doctest.TestResults(failed=0, attempted=1)


def test_failure_is_reported_and_counted(
    capsys: pytest.CaptureFixture[str],
) -> None:
    result: doctest.TestResults = run_doctests(_failing_example)
    report: str = capsys.readouterr().out

    assert result == doctest.TestResults(failed=1, attempted=1)
    assert "Failed example:" in report
    assert "2 + 2" in report
    assert "Expected:" in report


def test_target_without_examples_returns_zero_totals() -> None:
    assert run_doctests(_no_examples) == doctest.TestResults(
        failed=0,
        attempted=0,
    )


def test_class_and_method_examples_are_found_recursively() -> None:
    result: doctest.TestResults = run_doctests(_Calculator)

    assert result == doctest.TestResults(failed=0, attempted=3)


def test_default_and_custom_optionflags_control_matching(
    capsys: pytest.CaptureFixture[str],
) -> None:
    default_result: doctest.TestResults = run_doctests(_ellipsis_example)
    exact_result: doctest.TestResults = run_doctests(
        _ellipsis_example,
        optionflags=0,
    )
    capsys.readouterr()

    assert default_result == doctest.TestResults(failed=0, attempted=1)
    assert exact_result == doctest.TestResults(failed=1, attempted=1)


def test_target_module_globals_are_available_to_examples() -> None:
    assert run_doctests(_uses_module_global) == doctest.TestResults(
        failed=0,
        attempted=1,
    )


def test_each_call_uses_fresh_runner_state(
    capsys: pytest.CaptureFixture[str],
) -> None:
    failed_result: doctest.TestResults = run_doctests(_failing_example)
    capsys.readouterr()
    empty_result: doctest.TestResults = run_doctests(_no_examples)

    assert failed_result == doctest.TestResults(failed=1, attempted=1)
    assert empty_result == doctest.TestResults(failed=0, attempted=0)


def test_public_annotations_and_defaults_are_exact() -> None:
    assert get_type_hints(run_doctests) == {
        "target": object,
        "optionflags": int,
        "return": doctest.TestResults,
    }
    assert (
        inspect.signature(run_doctests).parameters["optionflags"].default
        == doctest.ELLIPSIS
    )
    assert get_type_hints(main) == {"return": type(None)}


def test_import_is_silent() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_10_testing_and_logging.exercise_01.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_guarded_module_demonstrates_the_runner() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "CH_10_testing_and_logging.exercise_01.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == "Attempted 1 doctest; 0 failed.\n"
    assert completed.stderr == ""
