"""Tests for runtime-deviation monitoring."""

import inspect
import warnings
from collections.abc import Callable, Iterator
from dataclasses import FrozenInstanceError

import pytest

from CH_12_performance.exercise_02.solution_00 import (
    RuntimeMonitor,
    RuntimeStats,
    monitor_runtime,
)


def clock(values: list[float]) -> Callable[[], float]:
    iterator: Iterator[float] = iter(values)
    return iterator.__next__


def test_preserves_free_function_metadata_and_signature() -> None:
    def original(value: int, *, scale: int = 1) -> int:
        """Return a scaled value."""
        return value * scale

    decorated: RuntimeMonitor[..., int] = monitor_runtime(
        clock=clock([0.0, 1.0]),
    )(original)

    assert decorated.__name__ == original.__name__
    assert decorated.__doc__ == original.__doc__
    assert decorated.__wrapped__ is original
    assert inspect.signature(decorated) == inspect.signature(original)


def test_wrapped_function_attributes_cannot_replace_monitor_state() -> None:
    def original() -> int:
        return 7

    collisions: dict[str, object] = {
        "_function": lambda: -1,
        "_clock": lambda: 999.0,
        "_max_deviation": 1_000.0,
        "stats": RuntimeStats(calls=40, total_seconds=40.0),
    }
    for name, value in collisions.items():
        setattr(original, name, value)

    intended_clock: Callable[[], float] = clock([0.0, 1.0, 2.0, 5.0])
    decorated: RuntimeMonitor[[], int] = monitor_runtime(
        clock=intended_clock,
        max_deviation=0.25,
    )(original)

    monitor_state: dict[str, object] = vars(decorated)
    assert (
        monitor_state["_function"],
        monitor_state["_clock"],
        monitor_state["_max_deviation"],
        monitor_state["stats"],
    ) == (original, intended_clock, 0.25, RuntimeStats(0, 0.0))
    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        assert decorated() == 7
    with pytest.warns(RuntimeWarning, match="deviated"):
        assert decorated() == 7

    assert decorated.stats == RuntimeStats(calls=2, total_seconds=4.0)


def test_decorated_method_binds_receiver_and_shares_stats() -> None:
    class Accumulator:
        def __init__(self, offset: int) -> None:
            self.offset: int = offset

        @monitor_runtime(clock=clock([0.0, 1.0, 2.0, 3.0]))
        def add(self, value: int, *, scale: int = 1) -> int:
            return self.offset + value * scale

    first: Accumulator = Accumulator(1)
    second: Accumulator = Accumulator(10)

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        assert first.add(2, scale=3) == 7
        assert second.add(2, scale=3) == 16

    expected: RuntimeStats = RuntimeStats(calls=2, total_seconds=2.0)
    assert Accumulator.add.stats == expected
    assert first.add.stats == expected
    assert second.add.stats == expected


def test_first_below_and_boundary_durations_emit_no_warning() -> None:
    monitor: RuntimeMonitor[[], None] = RuntimeMonitor(
        lambda: None,
        clock=clock([0.0, 2.0, 3.0, 5.5, 6.0, 9.375]),
        max_deviation=0.5,
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        monitor()
        monitor()
        monitor()


def test_third_duration_is_compared_with_prior_running_average() -> None:
    monitor: RuntimeMonitor[[], None] = RuntimeMonitor(
        lambda: None,
        clock=clock([0.0, 1.0, 2.0, 5.0, 6.0, 9.0]),
        max_deviation=0.25,
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", RuntimeWarning)
        monitor()
    with pytest.warns(RuntimeWarning, match="deviated"):
        monitor()
    with pytest.warns(RuntimeWarning, match="deviated"):
        monitor()

    assert monitor.stats == RuntimeStats(calls=3, total_seconds=7.0)


def test_warns_against_previous_running_average() -> None:
    @monitor_runtime(clock=clock([0.0, 1.0, 2.0, 4.0]), max_deviation=0.25)
    def operation() -> str:
        return "ok"

    assert operation() == "ok"
    with pytest.warns(RuntimeWarning, match="deviated"):
        assert operation() == "ok"

    assert operation.stats == RuntimeStats(calls=2, total_seconds=3.0)
    assert operation.stats.average_seconds == pytest.approx(1.5)


def test_duration_at_deviation_boundary_does_not_warn() -> None:
    monitor: RuntimeMonitor[[], None] = RuntimeMonitor(
        lambda: None,
        clock=clock([0.0, 2.0, 3.0, 6.0]),
        max_deviation=0.5,
    )

    monitor()
    monitor()

    assert monitor.stats == RuntimeStats(calls=2, total_seconds=5.0)


def test_failed_call_does_not_update_stats_or_sample_end_time() -> None:
    def fail() -> None:
        raise RuntimeError("boom")

    monitor: RuntimeMonitor[[], None] = RuntimeMonitor(
        fail,
        clock=clock([1.0]),
        max_deviation=0.25,
    )

    with pytest.raises(RuntimeError, match="boom"):
        monitor()

    assert monitor.stats == RuntimeStats(calls=0, total_seconds=0.0)


def test_clock_moving_backwards_does_not_update_stats() -> None:
    monitor: RuntimeMonitor[[], None] = RuntimeMonitor(
        lambda: None,
        clock=clock([2.0, 1.0]),
        max_deviation=0.25,
    )

    with pytest.raises(ValueError, match="clock moved backwards"):
        monitor()

    assert monitor.stats.calls == 0


@pytest.mark.parametrize("deviation", [-0.1, float("nan")])
def test_invalid_deviation_is_rejected(deviation: float) -> None:
    with pytest.raises(
        ValueError,
        match="max_deviation must not be negative",
    ):
        monitor_runtime(max_deviation=deviation)

    with pytest.raises(
        ValueError,
        match="max_deviation must not be negative",
    ):
        RuntimeMonitor(
            lambda: None,
            clock=lambda: 0.0,
            max_deviation=deviation,
        )


def test_runtime_stats_is_frozen_and_empty_average_is_zero() -> None:
    stats: RuntimeStats = RuntimeStats(calls=0, total_seconds=0.0)

    assert stats.average_seconds == 0.0
    with pytest.raises(FrozenInstanceError):
        stats.__setattr__("calls", 1)
