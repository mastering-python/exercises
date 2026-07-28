from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator
from itertools import islice as stdlib_islice
from pathlib import Path
from typing import cast

import pytest

from .solution_00 import islice


class OneShotIterable:
    def __init__(self, values: list[int]) -> None:
        self.values: list[int] = values
        self.iterations: int = 0

    def __iter__(self) -> Iterator[int]:
        self.iterations += 1
        if self.iterations > 1:
            raise AssertionError("iterable was iterated more than once")
        return iter(self.values)


class TrackingIterable:
    def __init__(self, values: list[int]) -> None:
        self.values: list[int] = values
        self.consumed: list[int] = []

    def __iter__(self) -> Iterator[int]:
        for value in self.values:
            self.consumed.append(value)
            yield value


class RaisingIterable:
    def __init__(self, error: RuntimeError) -> None:
        self.error: RuntimeError = error
        self.iterations: int = 0

    def __iter__(self) -> Iterator[int]:
        self.iterations += 1
        yield 1
        raise self.error


class FailOnIteration:
    def __init__(self) -> None:
        self.iterations: int = 0

    def __iter__(self) -> Iterator[int]:
        self.iterations += 1
        raise AssertionError("source must not be iterated")


class IndexCompatible:
    def __init__(self, value: int) -> None:
        self.value: int = value
        self.calls: int = 0

    def __index__(self) -> int:
        self.calls += 1
        return self.value


@pytest.mark.parametrize(
    ("start", "stop", "step"),
    [
        (0, 10, 1),
        (1, 10, 2),
        (3, 3, 1),
        (4, 50, 3),
        (10, 2, -1),
        (10, 1, -3),
        (3, 8, -1),
    ],
)
def test_islice_matches_list_slice_for_nonnegative_bounds(
    start: int,
    stop: int,
    step: int,
) -> None:
    values: list[int] = list(range(12))

    assert list(islice(values, start, stop, step)) == values[start:stop:step]


@pytest.mark.parametrize(
    ("values", "start", "stop", "step"),
    [
        ([], 0, 10, 1),
        ([], 10, 0, -1),
        ([1, 2, 3], 20, 30, 1),
        ([1, 2, 3], 20, 10, -1),
        ([1, 2, 3], 0, 20, -1),
    ],
)
def test_empty_and_out_of_range_slices(
    values: list[int],
    start: int,
    stop: int,
    step: int,
) -> None:
    assert list(islice(values, start, stop, step)) == values[start:stop:step]


@pytest.mark.parametrize(
    ("start", "stop", "step"),
    [
        (-1, -8, -1),
        (-2, -11, -2),
        (8, -20, -3),
        (-20, -1, -1),
    ],
)
def test_negative_step_supports_negative_bounds(
    start: int,
    stop: int,
    step: int,
) -> None:
    values: list[int] = list(range(10))

    assert list(islice(values, start, stop, step)) == values[start:stop:step]


def test_zero_step_raises_immediately_without_iterating_source() -> None:
    source: OneShotIterable = OneShotIterable([1, 2, 3])

    with pytest.raises(ValueError):
        islice(source, 0, 3, 0)

    assert source.iterations == 0


def test_step_defaults_to_one() -> None:
    assert list(islice(range(8), 2, 6)) == [2, 3, 4, 5]


@pytest.mark.parametrize(
    ("start", "stop", "step"),
    [
        (cast(int, 1.5), 4, 1),
        (4, cast(int, -0.5), -1),
        (4, 0, cast(int, -1.5)),
    ],
)
def test_invalid_indices_fail_before_source_iteration(
    start: int,
    stop: int,
    step: int,
) -> None:
    source: FailOnIteration = FailOnIteration()

    with pytest.raises(TypeError):
        islice(source, start, stop, step)

    assert source.iterations == 0


@pytest.mark.parametrize(
    ("start_value", "stop_value", "step_value", "expected"),
    [
        (1, 7, 2, [1, 3, 5]),
        (7, 1, -2, [7, 5, 3]),
    ],
)
def test_index_compatible_arguments_are_normalized(
    start_value: int,
    stop_value: int,
    step_value: int,
    expected: list[int],
) -> None:
    start: IndexCompatible = IndexCompatible(start_value)
    stop: IndexCompatible = IndexCompatible(stop_value)
    step: IndexCompatible = IndexCompatible(step_value)

    result: list[int] = list(
        islice(
            range(9),
            cast(int, start),
            cast(int, stop),
            cast(int, step),
        )
    )

    assert result == expected
    assert (start.calls, stop.calls, step.calls) == (1, 1, 1)


def test_index_compatible_zero_step_fails_before_source_iteration() -> None:
    source: FailOnIteration = FailOnIteration()
    step: IndexCompatible = IndexCompatible(0)

    with pytest.raises(ValueError):
        islice(source, 0, 3, cast(int, step))

    assert step.calls == 1
    assert source.iterations == 0


@pytest.mark.parametrize(
    ("start", "stop"),
    [
        (-1, 3),
        (0, -1),
        (-4, -1),
    ],
)
def test_positive_step_negative_indices_match_stdlib_errors(
    start: int,
    stop: int,
) -> None:
    with pytest.raises(ValueError) as expected_error:
        stdlib_islice([1, 2, 3], start, stop, 1)

    with pytest.raises(ValueError) as actual_error:
        islice([1, 2, 3], start, stop, 1)

    assert str(actual_error.value) == str(expected_error.value)


@pytest.mark.parametrize(
    ("start", "stop", "step"),
    [
        (1, 6, 2),
        (6, 1, -2),
    ],
)
def test_one_shot_iterable_is_iterated_once(
    start: int,
    stop: int,
    step: int,
) -> None:
    source: OneShotIterable = OneShotIterable(list(range(8)))

    assert list(islice(source, start, stop, step)) == source.values[start:stop:step]
    assert source.iterations == 1


def test_positive_step_consumes_lazily_and_only_to_stop() -> None:
    source: TrackingIterable = TrackingIterable(list(range(20)))
    result: Iterator[int] = islice(source, 2, 7, 2)

    assert source.consumed == []
    assert next(result) == 2
    assert source.consumed == [0, 1, 2]
    assert list(result) == [4, 6]
    assert source.consumed == list(range(7))


def test_negative_step_materializes_source_once_at_call_time() -> None:
    source: TrackingIterable = TrackingIterable(list(range(8)))

    result: Iterator[int] = islice(source, 6, 1, -2)

    assert source.consumed == list(range(8))
    assert list(result) == [6, 4, 2]


@pytest.mark.parametrize(
    ("start", "stop", "step"),
    [
        (0, 3, 1),
        (2, 0, -1),
    ],
)
def test_source_exception_propagates_and_source_is_iterated_once(
    start: int,
    stop: int,
    step: int,
) -> None:
    error: RuntimeError = RuntimeError("source failed")
    source: RaisingIterable = RaisingIterable(error)

    with pytest.raises(RuntimeError) as caught:
        list(islice(source, start, stop, step))

    assert caught.value is error
    assert source.iterations == 1


def test_import_is_silent() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_07_generators_and_coroutines.exercise_01.solution_00",
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout == ""
    assert completed.stderr == ""


def test_module_demonstration() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "CH_07_generators_and_coroutines.exercise_01.solution_00",
        ],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout == "[20, 19, 18, 17, 16, 15, 14, 13, 12, 11]\n"
    assert completed.stderr == ""
