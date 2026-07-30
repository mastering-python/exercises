"""Tests for source-line execution counts."""

import inspect

import pytest

from CH_11_debugging.exercise_03.solution_00 import (
    ExecutionCounts,
    count_executions,
)


def repeated(total: int) -> int:
    value: int = 0
    for number in range(total):
        value += number
    return value


def test_count_executions_reports_loop_line_frequency() -> None:
    source_lines: list[str]
    first_line: int
    source_lines, first_line = inspect.getsourcelines(repeated)
    offset: int = next(
        index for index, line in enumerate(source_lines) if "value += number" in line
    )
    loop_line: int = first_line + offset

    profile: ExecutionCounts[int] = count_executions(repeated, 4)

    assert profile.result == 6
    assert profile.counts[loop_line] == 4
    assert all(count > 0 for count in profile.counts.values())


def test_count_executions_propagates_failure() -> None:
    def fail() -> None:
        raise LookupError("boom")

    with pytest.raises(LookupError, match="boom"):
        count_executions(fail)


def test_count_executions_rejects_callable_without_source_file() -> None:
    with pytest.raises(ValueError, match="no inspectable source file"):
        count_executions(len, [])
