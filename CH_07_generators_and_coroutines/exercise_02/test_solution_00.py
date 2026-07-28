"""Tests for one-shot generator slicing."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

from CH_07_generators_and_coroutines.exercise_02.solution_00 import (
    SliceableGenerator,
)


def test_slices_consume_one_underlying_iterator_sequentially() -> None:
    values: SliceableGenerator[int] = SliceableGenerator(iter(range(30)))

    assert values[2:6] == [2, 3, 4, 5]
    assert values[0:3] == [6, 7, 8]


def test_positive_step_is_relative_to_current_position() -> None:
    values: SliceableGenerator[int] = SliceableGenerator(range(12))

    assert values[1:8:3] == [1, 4, 7]
    assert values[:2] == [8, 9]


def test_omitted_bounds_and_step_are_supported() -> None:
    values: SliceableGenerator[int] = SliceableGenerator(range(10))

    assert values[:3] == [0, 1, 2]
    assert values[1::2] == [4, 6, 8]


def test_empty_and_exhausted_slices_return_empty_lists() -> None:
    values: SliceableGenerator[int] = SliceableGenerator(range(3))

    assert values[0:0] == []
    assert values[:] == [0, 1, 2]
    assert values[:4] == []


@pytest.mark.parametrize(
    "invalid_slice",
    [
        slice(-1, 3),
        slice(0, -1),
        slice(-2, -1),
    ],
)
def test_negative_slice_bound_is_rejected_without_consuming(
    invalid_slice: slice,
) -> None:
    values: SliceableGenerator[int] = SliceableGenerator(range(5))

    with pytest.raises(ValueError, match="non-negative"):
        values[invalid_slice]

    assert values[:2] == [0, 1]


@pytest.mark.parametrize("step", [0, -1, -5])
def test_nonpositive_step_is_rejected_without_consuming(step: int) -> None:
    values: SliceableGenerator[int] = SliceableGenerator(range(5))

    with pytest.raises(ValueError, match="positive"):
        values[::step]

    assert values[:2] == [0, 1]


def test_integer_indexing_is_rejected_without_consuming() -> None:
    values: SliceableGenerator[int] = SliceableGenerator(range(5))

    with pytest.raises(TypeError, match="slices only"):
        values[cast(slice, 1)]

    assert values[:2] == [0, 1]


def test_import_is_silent() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_07_generators_and_coroutines.exercise_02.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_guarded_demo_is_bounded() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "CH_07_generators_and_coroutines.exercise_02.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert completed.returncode == 0
    assert completed.stdout == "[10, 11, 12, 13, 14, 15, 16, 17, 18, 19]\n"
    assert completed.stderr == ""
