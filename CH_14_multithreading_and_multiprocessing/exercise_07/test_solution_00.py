"""Tests for bounded deterministic parallel merge sort."""

from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path

import pytest

from .solution_00 import (
    merge,
    merge_sort,
    multiprocessing_merge_sort,
    parallel_merge_sort,
    split,
)

_REPOSITORY_ROOT: Path = Path(__file__).parents[2]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ([], [], []),
        ([1, 3], [2, 4], [1, 2, 3, 4]),
        ([1, 1], [1], [1, 1, 1]),
        ([-3, 8], [-4, 9], [-4, -3, 8, 9]),
    ],
)
def test_merge(
    left: list[int],
    right: list[int],
    expected: list[int],
) -> None:
    original_left: list[int] = left.copy()
    original_right: list[int] = right.copy()

    assert merge(left, right) == expected
    assert left == original_left
    assert right == original_right


def test_split_is_balanced_and_never_creates_empty_chunks() -> None:
    assert split([], 4) == []
    assert split([3, 2], 8) == [[3], [2]]
    assert split([1, 2, 3, 4, 5], 2) == [[1, 2, 3], [4, 5]]


@pytest.mark.parametrize("size", [0, -1])
def test_split_size_must_be_positive(size: int) -> None:
    with pytest.raises(ValueError, match=r"^size must be positive$"):
        split([1], size)


@pytest.mark.timeout(20)
def test_parallel_merge_sort_matches_builtin_without_mutation() -> None:
    values: list[int] = [5, -1, 5, 0, 9, 2, -7]

    assert parallel_merge_sort(
        values,
        max_workers=3,
        context=multiprocessing.get_context("spawn"),
    ) == sorted(values)
    assert multiprocessing_merge_sort(values) == sorted(values)
    assert values == [5, -1, 5, 0, 9, 2, -7]


def test_empty_parallel_sort_does_not_spawn_children() -> None:
    before: set[int] = {
        process.pid
        for process in multiprocessing.active_children()
        if process.pid is not None
    }

    assert parallel_merge_sort([], max_workers=8) == []
    assert {
        process.pid
        for process in multiprocessing.active_children()
        if process.pid is not None
    } == before


def test_sequential_merge_sort_handles_boundaries() -> None:
    assert merge_sort([]) == []
    assert merge_sort([1]) == [1]
    assert merge_sort((3, 1, 2)) == [1, 2, 3]


@pytest.mark.parametrize("max_workers", [0, -1])
def test_parallel_worker_count_must_be_positive(max_workers: int) -> None:
    with pytest.raises(ValueError, match=r"^max_workers must be positive$"):
        parallel_merge_sort([1], max_workers=max_workers)


@pytest.mark.parametrize("values", [[1, True], [1, "2"]])
def test_sort_rejects_non_integer_values(values: list[object]) -> None:
    with pytest.raises(TypeError, match=r"values must contain only integers"):
        parallel_merge_sort(values)  # type: ignore[arg-type]
