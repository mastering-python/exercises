"""Tests for deterministic callable timing."""

from collections.abc import Callable, Iterator
from dataclasses import FrozenInstanceError

import pytest

from CH_11_debugging.exercise_02.solution_00 import (
    CallTimer,
    TimedResult,
    measure_call,
)


def clock_from(values: list[float]) -> Callable[[], float]:
    iterator: Iterator[float] = iter(values)
    return iterator.__next__


def test_measure_returns_value_and_elapsed_seconds() -> None:
    timer: CallTimer = CallTimer(clock_from([10.0, 10.25]))

    def increment(value: int) -> int:
        return value + 1

    result: TimedResult[int] = timer.measure(increment, 4)

    assert result == TimedResult(value=5, seconds=0.25)


def test_measure_forwards_keyword_arguments() -> None:
    timer: CallTimer = CallTimer(clock_from([2.0, 2.0]))

    def concatenate(value: str, *, suffix: str) -> str:
        return value + suffix

    result: TimedResult[str] = timer.measure(
        concatenate,
        "a",
        suffix="b",
    )

    assert result == TimedResult(value="ab", seconds=0.0)


def test_measure_propagates_failure_without_sampling_end_time() -> None:
    timer: CallTimer = CallTimer(clock_from([1.0]))

    def fail() -> None:
        raise RuntimeError("failed")

    with pytest.raises(RuntimeError, match="failed"):
        timer.measure(fail)


def test_measure_rejects_clock_moving_backwards() -> None:
    timer: CallTimer = CallTimer(clock_from([5.0, 4.0]))

    with pytest.raises(ValueError, match="clock moved backwards"):
        timer.measure(lambda: None)


def test_timed_result_is_frozen() -> None:
    result: TimedResult[int] = TimedResult(value=1, seconds=0.5)

    with pytest.raises(FrozenInstanceError):
        result.__setattr__("seconds", 1.0)


def test_measure_call_returns_a_timed_result() -> None:
    result: TimedResult[int] = measure_call(sum, [1, 2, 3])

    assert result.value == 6
    assert result.seconds >= 0.0
