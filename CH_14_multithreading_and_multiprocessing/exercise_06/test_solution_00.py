"""Tests for allowlisted queue RPC workers."""

from __future__ import annotations

import multiprocessing
import sys
from multiprocessing.context import BaseContext
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest

from .solution_00 import (
    RPC_METHODS,
    RemoteCallError,
    RpcWorkerPool,
    UnknownMethodError,
)

_REPOSITORY_ROOT: Path = Path(__file__).parents[2]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))


def _child_pids() -> set[int]:
    return {
        process.pid
        for process in multiprocessing.active_children()
        if process.pid is not None
    }


def test_rpc_calls_only_registered_methods() -> None:
    assert tuple(RPC_METHODS) == ("add", "repeat")
    with RpcWorkerPool(worker_count=2) as rpc:
        assert rpc.call("add", 2, 5, timeout=5.0) == 7
        assert rpc.call("repeat", "ab", count=3, timeout=5.0) == "ababab"


@pytest.mark.parametrize("method", ["missing", "__import__", "__class__"])
def test_unknown_method_does_not_kill_worker(method: str) -> None:
    with RpcWorkerPool(worker_count=1) as rpc:
        with pytest.raises(UnknownMethodError, match=method):
            rpc.call(method, timeout=5.0)
        assert rpc.call("add", 1, 1, timeout=5.0) == 2


def test_remote_argument_error_does_not_kill_worker() -> None:
    with RpcWorkerPool(worker_count=1) as rpc:
        with pytest.raises(RemoteCallError, match=r"TypeError"):
            rpc.call("add", "one", 2, timeout=5.0)
        with pytest.raises(RemoteCallError, match=r"ValueError"):
            rpc.call("repeat", "x", count=-1, timeout=5.0)
        assert rpc.call("repeat", "x", count=2, timeout=5.0) == "xx"


def test_rpc_method_mapping_is_immutable() -> None:
    with pytest.raises(TypeError):
        RPC_METHODS["missing"] = lambda: None  # type: ignore[index]


@pytest.mark.timeout(20)
def test_rpc_context_reaps_children() -> None:
    before: set[int] = _child_pids()
    with RpcWorkerPool(
        worker_count=2,
        context=multiprocessing.get_context("spawn"),
    ) as rpc:
        assert rpc.call("add", 20, 22, timeout=5.0) == 42
    assert _child_pids() == before


@pytest.mark.parametrize("worker_count", [0, -1])
def test_worker_count_must_be_positive(worker_count: int) -> None:
    with pytest.raises(ValueError, match=r"^worker_count must be positive$"):
        RpcWorkerPool(worker_count=worker_count)


def test_forced_shutdown_cancels_queue_feeders() -> None:
    requests: MagicMock = MagicMock()
    replies: MagicMock = MagicMock()
    process: MagicMock = MagicMock()
    process.is_alive.return_value = True
    process.exitcode = -15
    context: MagicMock = MagicMock()
    context.Queue.side_effect = [requests, replies]
    context.Process.return_value = process
    rpc: RpcWorkerPool = RpcWorkerPool(
        worker_count=1,
        context=cast(BaseContext, context),
        shutdown_timeout=0.01,
    )

    with pytest.raises(TimeoutError, match=r"^RPC worker shutdown timed out$"):
        rpc.close()

    requests.cancel_join_thread.assert_called_once_with()
    replies.cancel_join_thread.assert_called_once_with()
    requests.join_thread.assert_not_called()
    replies.join_thread.assert_not_called()
