"""Tests for the generic persistent multiprocessing worker pool."""

from __future__ import annotations

import multiprocessing
import sys
from multiprocessing.context import BaseContext
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest

from .solution_00 import PersistentWorkerPool, WorkerError, square

_REPOSITORY_ROOT: Path = Path(__file__).parents[2]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))


def _child_pids() -> set[int]:
    return {
        process.pid
        for process in multiprocessing.active_children()
        if process.pid is not None
    }


@pytest.mark.timeout(20)
def test_pool_reuses_workers_and_preserves_map_order() -> None:
    before: set[int] = _child_pids()
    with PersistentWorkerPool(
        square,
        worker_count=2,
        context=multiprocessing.get_context("spawn"),
    ) as pool:
        first_pids: tuple[int, ...] = pool.worker_pids
        assert len(first_pids) == 2
        assert pool.map([3, 1, 2], timeout=5.0) == [9, 1, 4]
        assert pool.map([4], timeout=5.0) == [16]
        assert pool.worker_pids == first_pids
    assert _child_pids() == before


def test_result_caches_out_of_order_replies() -> None:
    with PersistentWorkerPool(square, worker_count=2) as pool:
        first: int = pool.submit(2)
        second: int = pool.submit(3)
        assert pool.result(second, timeout=5.0) == 9
        assert pool.result(first, timeout=5.0) == 4


def test_pool_propagates_failure_and_worker_continues() -> None:
    with PersistentWorkerPool(square, worker_count=1) as pool:
        bad_task: int = pool.submit(cast(int, "bad"))
        with pytest.raises(WorkerError, match=r"TypeError"):
            pool.result(bad_task, timeout=5.0)
        assert pool.map([5], timeout=5.0) == [25]


def test_close_is_idempotent_and_rejects_submission() -> None:
    pool: PersistentWorkerPool[int, int] = PersistentWorkerPool(
        square,
        worker_count=1,
    )
    pool.close()
    pool.close()

    with pytest.raises(RuntimeError, match=r"pool is closed"):
        pool.submit(2)
    assert all(not process.is_alive() for process in pool.workers)


@pytest.mark.parametrize("worker_count", [0, -1])
def test_worker_count_must_be_positive(worker_count: int) -> None:
    with pytest.raises(ValueError, match=r"^worker_count must be positive$"):
        PersistentWorkerPool(square, worker_count=worker_count)


@pytest.mark.parametrize("timeout", [0.0, -1.0])
def test_result_timeout_must_be_positive(timeout: float) -> None:
    with PersistentWorkerPool(square, worker_count=1) as pool:
        task_id: int = pool.submit(2)
        with pytest.raises(ValueError, match=r"^timeout must be positive$"):
            pool.result(task_id, timeout=timeout)


def test_forced_shutdown_cancels_queue_feeders() -> None:
    tasks: MagicMock = MagicMock()
    replies: MagicMock = MagicMock()
    process: MagicMock = MagicMock()
    process.is_alive.return_value = True
    process.exitcode = -15
    context: MagicMock = MagicMock()
    context.Queue.side_effect = [tasks, replies]
    context.Process.return_value = process
    pool: PersistentWorkerPool[int, int] = PersistentWorkerPool(
        square,
        worker_count=1,
        context=cast(BaseContext, context),
        shutdown_timeout=0.01,
    )

    with pytest.raises(TimeoutError, match=r"^worker pool shutdown timed out$"):
        pool.close()

    tasks.cancel_join_thread.assert_called_once_with()
    replies.cancel_join_thread.assert_called_once_with()
    tasks.join_thread.assert_not_called()
    replies.join_thread.assert_not_called()
