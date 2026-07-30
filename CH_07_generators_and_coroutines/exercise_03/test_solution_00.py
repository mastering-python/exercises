"""Tests for the infinite Fibonacci generator."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator
from itertools import islice
from pathlib import Path
from typing import get_type_hints

from CH_07_generators_and_coroutines.exercise_03.solution_00 import fibonacci


def test_first_ten_fibonacci_numbers() -> None:
    assert list(islice(fibonacci(), 10)) == [
        0,
        1,
        1,
        2,
        3,
        5,
        8,
        13,
        21,
        34,
    ]


def test_generator_instances_advance_independently() -> None:
    first: Iterator[int] = fibonacci()
    second: Iterator[int] = fibonacci()

    assert [next(first), next(first), next(second), next(first)] == [0, 1, 0, 1]


def test_hundredth_value_is_generated_iteratively() -> None:
    hundredth: int = next(islice(fibonacci(), 100, 101))

    assert hundredth == 354224848179261915075


def test_return_type_is_explicit() -> None:
    assert get_type_hints(fibonacci)["return"] == Iterator[int]


def test_import_is_silent() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_07_generators_and_coroutines.exercise_03.solution_00",
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
            "CH_07_generators_and_coroutines.exercise_03.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert completed.returncode == 0
    assert completed.stdout == "[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]\n"
    assert completed.stderr == ""
