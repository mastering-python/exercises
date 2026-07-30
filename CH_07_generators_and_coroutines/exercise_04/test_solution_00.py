"""Tests for the incremental prime sieve."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator
from itertools import islice
from pathlib import Path
from typing import get_type_hints

from CH_07_generators_and_coroutines.exercise_04.solution_00 import (
    generate_primes,
)


def _is_prime(candidate: int) -> bool:
    if candidate < 2:
        return False
    divisor: int = 2
    while divisor * divisor <= candidate:
        if candidate % divisor == 0:
            return False
        divisor += 1
    return True


def _first_primes(count: int) -> list[int]:
    primes: list[int] = []
    candidate: int = 2
    while len(primes) < count:
        if _is_prime(candidate):
            primes.append(candidate)
        candidate += 1
    return primes


def test_first_twenty_primes() -> None:
    assert list(islice(generate_primes(), 20)) == [
        2,
        3,
        5,
        7,
        11,
        13,
        17,
        19,
        23,
        29,
        31,
        37,
        41,
        43,
        47,
        53,
        59,
        61,
        67,
        71,
    ]


def test_first_two_hundred_match_trial_division_oracle() -> None:
    assert list(islice(generate_primes(), 200)) == _first_primes(200)


def test_generator_instances_do_not_share_sieve_state() -> None:
    first: Iterator[int] = generate_primes()
    second: Iterator[int] = generate_primes()

    assert [next(first), next(first), next(second), next(first)] == [2, 3, 2, 5]


def test_return_type_is_explicit() -> None:
    assert get_type_hints(generate_primes)["return"] == Iterator[int]


def test_import_is_silent() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_07_generators_and_coroutines.exercise_04.solution_00",
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
            "CH_07_generators_and_coroutines.exercise_04.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert completed.returncode == 0
    assert completed.stdout == (
        "[2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71]\n"
    )
    assert completed.stderr == ""
