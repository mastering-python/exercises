"""Tests for the recursive doctest runner."""

from __future__ import annotations

import doctest
import inspect
import linecache
import pdb
import subprocess
import sys
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import TextIO, get_type_hints

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


def _keyboard_interrupt_example() -> None:
    """
    >>> raise KeyboardInterrupt
    """


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


def test_passing_and_empty_targets_are_silent_with_verbose_argv(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["pytest", "-v"])

    passing_result: doctest.TestResults = run_doctests(_passing_example)
    empty_result: doctest.TestResults = run_doctests(_no_examples)

    assert passing_result == doctest.TestResults(failed=0, attempted=1)
    assert empty_result == doctest.TestResults(failed=0, attempted=0)
    assert capsys.readouterr().out == ""


def test_target_module_globals_are_available_to_examples() -> None:
    assert run_doctests(_uses_module_global) == doctest.TestResults(
        failed=0,
        attempted=1,
    )


def test_locally_defined_function_can_reference_itself() -> None:
    def local_double(value: int) -> int:
        """
        >>> local_double(5)
        10
        """
        return value * 2

    assert run_doctests(local_double) == doctest.TestResults(
        failed=0,
        attempted=1,
    )


def test_locally_defined_class_can_reference_itself() -> None:
    class LocalMultiplier:
        """
        >>> LocalMultiplier(6).double()
        12
        """

        def __init__(self, value: int) -> None:
            self.value: int = value

        def double(self) -> int:
            """Return twice the configured value."""
            return self.value * 2

    assert run_doctests(LocalMultiplier) == doctest.TestResults(
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


def test_keyboard_interrupt_propagates_without_leaving_runner_state() -> None:
    with pytest.raises(KeyboardInterrupt):
        run_doctests(_keyboard_interrupt_example)

    assert run_doctests(_passing_example) == doctest.TestResults(
        failed=0,
        attempted=1,
    )


def test_concurrent_calls_do_not_overlap_and_restore_process_globals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_run: Callable[..., doctest.TestResults] = doctest.DocTestRunner.run
    original_stdout: TextIO = sys.stdout
    original_displayhook: Callable[[object], None] = sys.displayhook
    original_set_trace: Callable[..., object] = pdb.set_trace
    original_getlines: Callable[..., list[str]] = linecache.getlines
    first_entered: threading.Event = threading.Event()
    second_entered: threading.Event = threading.Event()
    second_started: threading.Event = threading.Event()
    release_first: threading.Event = threading.Event()
    state_lock: threading.Lock = threading.Lock()
    active_runners: int = 0
    maximum_active_runners: int = 0
    entry_count: int = 0

    def instrumented_run(
        self: doctest.DocTestRunner,
        *args: object,
        **kwargs: object,
    ) -> doctest.TestResults:
        nonlocal active_runners, entry_count, maximum_active_runners

        with state_lock:
            active_runners += 1
            entry_count += 1
            current_entry: int = entry_count
            maximum_active_runners = max(
                maximum_active_runners,
                active_runners,
            )

        if current_entry == 1:
            first_entered.set()
            if not release_first.wait(timeout=2):
                raise TimeoutError("first doctest runner was not released")
        else:
            second_entered.set()

        try:
            return original_run(self, *args, **kwargs)
        finally:
            with state_lock:
                active_runners -= 1

    def run_second_call() -> doctest.TestResults:
        second_started.set()
        return run_doctests(_passing_example)

    monkeypatch.setattr(doctest.DocTestRunner, "run", instrumented_run)
    executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=2)
    try:
        first_future: Future[doctest.TestResults] = executor.submit(
            run_doctests,
            _passing_example,
        )
        assert first_entered.wait(timeout=1)

        second_future: Future[doctest.TestResults] = executor.submit(
            run_second_call,
        )
        assert second_started.wait(timeout=1)
        assert not second_entered.wait(timeout=0.1)
        release_first.set()

        assert first_future.result(timeout=2) == doctest.TestResults(0, 1)
        assert second_future.result(timeout=2) == doctest.TestResults(0, 1)
    finally:
        release_first.set()
        executor.shutdown(wait=True)

    assert second_entered.is_set()
    assert maximum_active_runners == 1
    assert sys.stdout is original_stdout
    assert sys.displayhook is original_displayhook
    assert pdb.set_trace is original_set_trace
    assert linecache.getlines is original_getlines


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
