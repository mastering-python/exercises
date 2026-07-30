"""Tests for canonical flat thread and process file-size workers."""

from __future__ import annotations

import multiprocessing
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from . import solution_00
from .solution_00 import multiprocessing_total_size, threaded_total_size

_REPOSITORY_ROOT: Path = Path(__file__).parents[2]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


@pytest.mark.timeout(20)
def test_thread_and_process_totals_match(tmp_path: Path) -> None:
    _write(tmp_path / "a.bin", b"12")
    _write(tmp_path / "b.bin", b"34567")
    _write(tmp_path / "nested" / "ignored.bin", b"ignored-data")
    outside: Path = tmp_path.parent / f"{tmp_path.name}-outside.bin"
    _write(outside, b"outside")
    (tmp_path / "ignored-link.bin").symlink_to(outside)

    assert threaded_total_size(tmp_path, worker_count=2) == 7
    assert (
        multiprocessing_total_size(
            tmp_path,
            worker_count=2,
            context=multiprocessing.get_context("spawn"),
        )
        == 7
    )


@pytest.mark.parametrize("function", [threaded_total_size, multiprocessing_total_size])
def test_apis_return_zero_for_empty_directory(
    function: Callable[..., int],
    tmp_path: Path,
) -> None:
    assert function(tmp_path) == 0


@pytest.mark.parametrize("function", [threaded_total_size, multiprocessing_total_size])
def test_apis_reject_non_directories(
    function: Callable[..., int],
    tmp_path: Path,
) -> None:
    path: Path = tmp_path / "file"
    _write(path, b"x")

    with pytest.raises(NotADirectoryError, match=rf"^{path} is not a directory$"):
        function(path)


@pytest.mark.parametrize("function", [threaded_total_size, multiprocessing_total_size])
@pytest.mark.parametrize("worker_count", [0, -1])
def test_worker_count_must_be_positive(
    function: Callable[..., int],
    worker_count: int,
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match=r"^worker_count must be positive$"):
        function(tmp_path, worker_count=worker_count)


def test_thread_worker_failure_propagates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_path: Path = tmp_path / "file.bin"
    _write(file_path, b"value")

    def fail(path: Path) -> int:
        raise OSError(f"cannot stat {path.name}")

    monkeypatch.setattr(solution_00, "_stat_size", fail)

    with pytest.raises(OSError, match=r"^cannot stat file\.bin$"):
        threaded_total_size(tmp_path, worker_count=2)
