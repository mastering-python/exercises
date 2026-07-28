"""Tests for delayed stalled-call diagnostics."""

import faulthandler
import subprocess
import sys

import pytest

from CH_11_debugging.exercise_01.solution_00 import (
    run_with_timeout_diagnostics,
)


def test_returns_value_and_forwards_arguments(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[tuple[str, object]] = []

    def schedule(
        timeout: float,
        repeat: bool = False,
        file: object | None = None,
        exit: bool = False,
    ) -> None:
        events.append(("scheduled", (timeout, repeat, file, exit)))

    def cancel() -> None:
        events.append(("cancelled", None))

    monkeypatch.setattr(faulthandler, "dump_traceback_later", schedule)
    monkeypatch.setattr(faulthandler, "cancel_dump_traceback_later", cancel)

    def combine(prefix: str, *, number: int) -> str:
        return f"{prefix}-{number}"

    result: str = run_with_timeout_diagnostics(
        combine,
        0.5,
        "item",
        number=3,
    )

    assert result == "item-3"
    assert events == [
        ("scheduled", (0.5, False, None, False)),
        ("cancelled", None),
    ]


def test_diagnostic_is_cancelled_when_function_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    def schedule(
        timeout: float,
        repeat: bool = False,
        file: object | None = None,
        exit: bool = False,
    ) -> None:
        del timeout, repeat, file, exit
        events.append("scheduled")

    def cancel() -> None:
        events.append("cancelled")

    monkeypatch.setattr(faulthandler, "dump_traceback_later", schedule)
    monkeypatch.setattr(faulthandler, "cancel_dump_traceback_later", cancel)

    def fail() -> None:
        raise LookupError("boom")

    with pytest.raises(LookupError, match="boom"):
        run_with_timeout_diagnostics(fail, 0.1)

    assert events == ["scheduled", "cancelled"]


@pytest.mark.parametrize("timeout", [0.0, -0.1, float("nan")])
def test_timeout_must_be_positive(timeout: float) -> None:
    with pytest.raises(ValueError, match="timeout must be positive"):
        run_with_timeout_diagnostics(lambda: None, timeout)


@pytest.mark.integration
def test_real_timeout_prints_stalled_function() -> None:
    source: str = """
import time
from CH_11_debugging.exercise_01.solution_00 import (
    run_with_timeout_diagnostics,
)

def stalled() -> None:
    time.sleep(0.10)

run_with_timeout_diagnostics(stalled, 0.01)
"""
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-c", source],
        text=True,
        capture_output=True,
        check=False,
        timeout=2,
    )

    assert completed.returncode == 0
    assert "Timeout" in completed.stderr
    assert "stalled" in completed.stderr


def test_module_import_is_silent() -> None:
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_11_debugging.exercise_01.solution_00",
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=2,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
