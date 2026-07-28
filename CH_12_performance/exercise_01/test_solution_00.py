"""Tests for sampled memory-growth monitoring."""

import inspect
import warnings
from collections.abc import Callable, Iterator

import pytest

from CH_12_performance.exercise_01.solution_00 import (
    MemoryGrowthMonitor,
    monitor_memory_growth,
)


def sampler(values: list[int]) -> Callable[[], int]:
    iterator: Iterator[int] = iter(values)
    return iterator.__next__


def test_preserves_free_function_metadata_and_signature() -> None:
    def original(value: int, *, scale: int = 1) -> int:
        """Return a scaled value."""
        return value * scale

    decorated: MemoryGrowthMonitor[..., int] = monitor_memory_growth(
        sampler=lambda: 100,
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
        "_sampler": lambda: 999,
        "_previous": 100,
        "_tolerance_bytes": 1_000,
    }
    for name, value in collisions.items():
        setattr(original, name, value)

    intended_sampler: Callable[[], int] = sampler([100, 120])
    decorated: MemoryGrowthMonitor[[], int] = monitor_memory_growth(
        sampler=intended_sampler,
        tolerance_bytes=5,
    )(original)

    monitor_state: dict[str, object] = vars(decorated)
    assert (
        monitor_state["_function"],
        monitor_state["_sampler"],
        monitor_state["_previous"],
        monitor_state["_tolerance_bytes"],
    ) == (original, intended_sampler, None, 5)
    with warnings.catch_warnings():
        warnings.simplefilter("error", ResourceWarning)
        assert decorated() == 7
    with pytest.warns(ResourceWarning, match="grew by 20 bytes"):
        assert decorated() == 7


def test_decorated_method_binds_receiver_and_shares_samples() -> None:
    class Accumulator:
        def __init__(self, offset: int) -> None:
            self.offset: int = offset

        @monitor_memory_growth(
            sampler=sampler([100, 120]),
            tolerance_bytes=5,
        )
        def add(self, value: int, *, scale: int = 1) -> int:
            return self.offset + value * scale

    first: Accumulator = Accumulator(1)
    second: Accumulator = Accumulator(10)

    with warnings.catch_warnings():
        warnings.simplefilter("error", ResourceWarning)
        assert first.add(2, scale=3) == 7
    with pytest.warns(ResourceWarning, match="grew by 20 bytes"):
        assert second.add(2, scale=3) == 16


def test_first_below_boundary_and_decrease_emit_no_warning() -> None:
    monitor: MemoryGrowthMonitor[[], None] = MemoryGrowthMonitor(
        lambda: None,
        sampler=sampler([100, 104, 109, 90]),
        tolerance_bytes=5,
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", ResourceWarning)
        monitor()
        monitor()
        monitor()
        monitor()


def test_warns_only_after_growth_above_tolerance() -> None:
    @monitor_memory_growth(
        sampler=sampler([100, 104, 120]),
        tolerance_bytes=5,
    )
    def value() -> int:
        return 7

    assert value() == 7
    assert value() == 7
    with pytest.warns(ResourceWarning, match="grew by 16 bytes"):
        assert value() == 7


def test_decrease_does_not_warn() -> None:
    monitor: MemoryGrowthMonitor[[], int] = MemoryGrowthMonitor(
        lambda: 1,
        sampler=sampler([100, 50]),
        tolerance_bytes=0,
    )

    assert monitor() == 1
    assert monitor() == 1


def test_failed_call_does_not_consume_a_sample() -> None:
    sample_count: int = 0

    def sample() -> int:
        nonlocal sample_count
        sample_count += 1
        return 10

    def fail() -> None:
        raise RuntimeError("boom")

    monitor: MemoryGrowthMonitor[[], None] = MemoryGrowthMonitor(
        fail,
        sampler=sample,
    )

    with pytest.raises(RuntimeError, match="boom"):
        monitor()

    assert sample_count == 0


def test_sampler_failure_preserves_previous_successful_sample() -> None:
    calls: int = 0

    def sample() -> int:
        nonlocal calls
        calls += 1
        if calls == 1:
            return 100
        if calls == 2:
            raise RuntimeError("sampler failed")
        return 120

    monitor: MemoryGrowthMonitor[[], None] = MemoryGrowthMonitor(
        lambda: None,
        sampler=sample,
    )

    monitor()
    with pytest.raises(RuntimeError, match="sampler failed"):
        monitor()
    with pytest.warns(ResourceWarning, match="grew by 20 bytes"):
        monitor()


@pytest.mark.parametrize("tolerance", [-1, -10])
def test_negative_tolerance_is_rejected(tolerance: int) -> None:
    with pytest.raises(
        ValueError,
        match="tolerance_bytes must not be negative",
    ):
        monitor_memory_growth(tolerance_bytes=tolerance)

    with pytest.raises(
        ValueError,
        match="tolerance_bytes must not be negative",
    ):
        MemoryGrowthMonitor(
            lambda: None,
            sampler=lambda: 0,
            tolerance_bytes=tolerance,
        )
