"""Tests for checked native signed-64-bit summation."""

from __future__ import annotations

import ctypes
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import cast

import pytest

from CH_17_c_and_cpp_extensions.exercise_02.solution_00 import custom_sum
from CH_17_c_and_cpp_extensions.native_build import build_extension

_LONG_LONG_BITS: int = ctypes.sizeof(ctypes.c_longlong) * 8
_LONG_LONG_MIN: int = -(1 << (_LONG_LONG_BITS - 1))
_LONG_LONG_MAX: int = (1 << (_LONG_LONG_BITS - 1)) - 1


@pytest.fixture(scope="module")
def native_module(
    tmp_path_factory: pytest.TempPathFactory,
) -> ModuleType:
    build_root: Path = tmp_path_factory.mktemp("safe-sum")
    source: Path = Path(__file__).with_name("safe_sum.c")
    return build_extension("_safe_sum", source, build_root)


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        ([], 0),
        ([1, -2, 3], 2),
        ([_LONG_LONG_MAX], _LONG_LONG_MAX),
        ([_LONG_LONG_MIN], _LONG_LONG_MIN),
    ],
)
def test_custom_sum_handles_normal_empty_and_limit_values(
    values: list[int],
    expected: int,
    native_module: ModuleType,
) -> None:
    original: list[int] = values.copy()

    assert custom_sum(values, native_module=native_module) == expected
    assert values == original


@pytest.mark.parametrize("value", [True, False, "bad", 1.5])
def test_custom_sum_rejects_booleans_and_non_integers_before_native_call(
    value: object,
) -> None:
    called: list[bool] = []
    fake_module: ModuleType = ModuleType("_must_not_run")

    def forbidden(values: Sequence[int]) -> int:
        del values
        called.append(True)
        return 0

    fake_module.__dict__["custom_sum"] = forbidden
    values: Sequence[int] = cast(Sequence[int], [value])

    with pytest.raises(TypeError, match="integers"):
        custom_sum(values, native_module=fake_module)

    assert called == []


@pytest.mark.parametrize("value", [1 << 100, -(1 << 100)])
def test_custom_sum_preserves_each_conversion_overflow(
    value: int,
    native_module: ModuleType,
) -> None:
    with pytest.raises(OverflowError):
        custom_sum([value], native_module=native_module)


def test_custom_sum_detects_cumulative_overflow(
    native_module: ModuleType,
) -> None:
    with pytest.raises(OverflowError, match="cumulative overflow"):
        custom_sum([_LONG_LONG_MAX, 1, -1], native_module=native_module)


def test_custom_sum_detects_cumulative_underflow(
    native_module: ModuleType,
) -> None:
    with pytest.raises(OverflowError, match="cumulative underflow"):
        custom_sum([_LONG_LONG_MIN, -1, 1], native_module=native_module)


@pytest.mark.parametrize(
    "values",
    [
        [_LONG_LONG_MAX, -_LONG_LONG_MAX],
        [-_LONG_LONG_MAX, _LONG_LONG_MAX],
        [_LONG_LONG_MIN, _LONG_LONG_MAX],
    ],
)
def test_custom_sum_allows_in_range_cancellation(
    values: list[int],
    native_module: ModuleType,
) -> None:
    assert custom_sum(values, native_module=native_module) == sum(values)


def test_native_extension_preserves_direct_conversion_errors(
    native_module: ModuleType,
) -> None:
    with pytest.raises(TypeError):
        native_module.custom_sum([1, "bad", 2])
    with pytest.raises(TypeError, match="booleans"):
        native_module.custom_sum([True])
    with pytest.raises(OverflowError):
        native_module.custom_sum([1 << 100])
    with pytest.raises(TypeError):
        native_module.custom_sum(42)


def test_custom_sum_rejects_invalid_native_result() -> None:
    fake_module: ModuleType = ModuleType("_invalid_result")

    def invalid_sum(values: Sequence[int]) -> bool:
        return bool(values)

    fake_module.__dict__["custom_sum"] = invalid_sum

    with pytest.raises(TypeError, match="non-integer"):
        custom_sum([1], native_module=fake_module)


def test_import_is_silent() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_17_c_and_cpp_extensions.exercise_02.solution_00",
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
            "CH_17_c_and_cpp_extensions.exercise_02.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert completed.returncode == 0
    assert completed.stdout == "6\n"
    assert completed.stderr == ""
