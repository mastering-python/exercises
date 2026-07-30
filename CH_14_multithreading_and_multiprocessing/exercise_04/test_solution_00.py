"""Tests for recursive persistent thread and process schedulers."""

from __future__ import annotations

import multiprocessing
import queue
import sys
from collections.abc import Callable
from multiprocessing.context import BaseContext
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest

from . import solution_00
from .solution_00 import (
    WorkerScanError,
    multiprocessing_recursive_size,
    threaded_recursive_size,
)

_REPOSITORY_ROOT: Path = Path(__file__).parents[2]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _child_pids() -> set[int]:
    return {
        process.pid
        for process in multiprocessing.active_children()
        if process.pid is not None
    }


@pytest.mark.timeout(20)
def test_recursive_apis_find_dynamically_enqueued_directories(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "root.bin", b"12")
    _write(tmp_path / "one" / "child.bin", b"345")
    _write(tmp_path / "one" / "two" / "deep.bin", b"67890")
    outside: Path = tmp_path.parent / f"{tmp_path.name}-outside"
    _write(outside / "ignored.bin", b"outside")
    (tmp_path / "directory-link").symlink_to(outside, target_is_directory=True)

    assert threaded_recursive_size(tmp_path, worker_count=3, timeout=5.0) == 10
    assert (
        multiprocessing_recursive_size(
            tmp_path,
            worker_count=2,
            timeout=5.0,
            context=multiprocessing.get_context("spawn"),
        )
        == 10
    )


@pytest.mark.parametrize(
    "function",
    [threaded_recursive_size, multiprocessing_recursive_size],
)
def test_recursive_apis_return_zero_for_empty_directory(
    function: Callable[..., int],
    tmp_path: Path,
) -> None:
    assert function(tmp_path) == 0


@pytest.mark.parametrize(
    "function",
    [threaded_recursive_size, multiprocessing_recursive_size],
)
def test_recursive_apis_reject_non_directories(
    function: Callable[..., int],
    tmp_path: Path,
) -> None:
    path: Path = tmp_path / "file"
    _write(path, b"x")

    with pytest.raises(NotADirectoryError, match=rf"^{path} is not a directory$"):
        function(path)


@pytest.mark.parametrize("timeout", [0.0, -1.0])
def test_timeout_must_be_positive(tmp_path: Path, timeout: float) -> None:
    with pytest.raises(ValueError, match=r"^timeout must be positive$"):
        threaded_recursive_size(tmp_path, timeout=timeout)


def test_thread_worker_failure_propagates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(tmp_path / "file.bin", b"value")

    def fail(directory: Path) -> solution_00.ScanResult:
        raise OSError(f"cannot scan {directory.name}")

    monkeypatch.setattr(solution_00, "_scan_directory", fail)

    with pytest.raises(WorkerScanError, match=r"OSError: cannot scan"):
        threaded_recursive_size(tmp_path, worker_count=2, timeout=2.0)


def test_scheduler_reports_all_worker_failures_deterministically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first: Path = tmp_path / "first"
    second: Path = tmp_path / "second"
    first.mkdir()
    second.mkdir()

    def fail_children(directory: Path) -> solution_00.ScanResult:
        if directory == tmp_path:
            return solution_00.ScanResult(directory, (second, first), 0)
        raise OSError(f"cannot scan {directory.name}")

    monkeypatch.setattr(solution_00, "_scan_directory", fail_children)

    with pytest.raises(WorkerScanError) as captured:
        threaded_recursive_size(tmp_path, worker_count=2, timeout=2.0)

    assert tuple(failure.directory for failure in captured.value.failures) == (
        first,
        second,
    )


@pytest.mark.timeout(20)
def test_process_workers_are_reaped(tmp_path: Path) -> None:
    _write(tmp_path / "nested" / "file.bin", b"value")
    before: set[int] = _child_pids()

    assert (
        multiprocessing_recursive_size(
            tmp_path,
            worker_count=2,
            timeout=5.0,
            context=multiprocessing.get_context("spawn"),
        )
        == 5
    )
    assert _child_pids() == before


def test_forced_process_cleanup_cancels_queue_feeders(tmp_path: Path) -> None:
    tasks: MagicMock = MagicMock()
    results: MagicMock = MagicMock()
    results.get.side_effect = queue.Empty
    process: MagicMock = MagicMock()
    process.is_alive.return_value = True
    process.exitcode = -15
    context: MagicMock = MagicMock()
    context.Queue.side_effect = [tasks, results]
    context.Process.return_value = process

    with pytest.raises(TimeoutError, match=r"^recursive scan timed out$"):
        multiprocessing_recursive_size(
            tmp_path,
            worker_count=1,
            timeout=0.01,
            context=cast(BaseContext, context),
        )

    tasks.cancel_join_thread.assert_called_once_with()
    results.cancel_join_thread.assert_called_once_with()
    tasks.join_thread.assert_not_called()
    results.join_thread.assert_not_called()
