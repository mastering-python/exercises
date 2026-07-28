"""Tests for ctypes, CFFI, and CPython-extension qsort paths."""

from __future__ import annotations

import ctypes
import subprocess
import sys
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

from CH_17_c_and_cpp_extensions.exercise_01.solution_00 import (
    qsort_cffi,
    qsort_ctypes,
    qsort_native,
)
from CH_17_c_and_cpp_extensions.native_build import build_extension

Sorter = Callable[[Sequence[int]], list[int]]

_C_INT_BITS: int = ctypes.sizeof(ctypes.c_int) * 8
_C_INT_MIN: int = -(1 << (_C_INT_BITS - 1))
_C_INT_MAX: int = (1 << (_C_INT_BITS - 1)) - 1


@pytest.fixture(scope="module")
def native_module(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[ModuleType]:
    build_root: Path = tmp_path_factory.mktemp("native-qsort")
    source: Path = Path(__file__).with_name("native_qsort.c")
    yield build_extension("_native_qsort", source, build_root)


def _sorters(native_module: ModuleType) -> tuple[Sorter, Sorter, Sorter]:
    def sort_native(values: Sequence[int]) -> list[int]:
        return qsort_native(values, native_module=native_module)

    return qsort_ctypes, qsort_cffi, sort_native


@pytest.mark.parametrize(
    "values",
    [
        [],
        [1],
        [4, -1, 4, 0, 2],
        [_C_INT_MIN, _C_INT_MAX, 0, _C_INT_MIN, _C_INT_MAX],
    ],
)
def test_all_qsort_paths_match_builtin_without_mutating_input(
    values: list[int],
    native_module: ModuleType,
) -> None:
    expected: list[int] = sorted(values)
    original: list[int] = values.copy()

    for sorter in _sorters(native_module):
        assert sorter(values) == expected
        assert values == original


def test_all_qsort_paths_accept_other_integer_sequences(
    native_module: ModuleType,
) -> None:
    values: tuple[int, ...] = (3, 1, 2)

    for sorter in _sorters(native_module):
        assert sorter(values) == [1, 2, 3]


@pytest.mark.parametrize("value", [_C_INT_MIN - 1, _C_INT_MAX + 1])
def test_all_qsort_paths_reject_values_outside_c_int_range(
    value: int,
    native_module: ModuleType,
) -> None:
    for sorter in _sorters(native_module):
        with pytest.raises(OverflowError, match="outside C int range"):
            sorter([value])


@pytest.mark.parametrize("value", [True, False, "2", 2.5])
def test_all_qsort_paths_reject_booleans_and_non_integers(
    value: object,
    native_module: ModuleType,
) -> None:
    values: Sequence[int] = cast(Sequence[int], [value])

    for sorter in _sorters(native_module):
        with pytest.raises(TypeError, match="integers"):
            sorter(values)


def test_native_extension_preserves_direct_conversion_errors(
    native_module: ModuleType,
) -> None:
    with pytest.raises(TypeError):
        native_module.sort_ints(["bad"])
    with pytest.raises(TypeError, match="booleans"):
        native_module.sort_ints([True])
    with pytest.raises(OverflowError):
        native_module.sort_ints([_C_INT_MAX + 1])
    with pytest.raises(TypeError):
        native_module.sort_ints(42)


def test_import_is_silent() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_17_c_and_cpp_extensions.exercise_01.solution_00",
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


def test_guarded_demo_builds_only_in_a_temporary_directory() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "CH_17_c_and_cpp_extensions.exercise_01.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0
    assert completed.stdout == "[-1, 2, 3]\n[-1, 2, 3]\n[-1, 2, 3]\n"
    assert completed.stderr == ""
