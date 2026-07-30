"""Allowlisted request/reply RPC over persistent multiprocessing queues."""

from __future__ import annotations

import math
import multiprocessing
import queue
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from multiprocessing.context import BaseContext
from time import monotonic
from types import MappingProxyType, TracebackType
from typing import Protocol, cast

__all__: list[str] = [
    "RPC_METHODS",
    "RemoteCallError",
    "RpcFailure",
    "RpcRequest",
    "RpcSuccess",
    "RpcWorkerPool",
    "StopRequest",
    "UnknownMethodError",
    "add",
    "repeat",
]


def add(left: int, right: int) -> int:
    """Return the sum of two integers."""

    return left + right


def repeat(value: str, *, count: int) -> str:
    """Repeat ``value`` ``count`` times."""

    if count < 0:
        raise ValueError("count must not be negative")
    return value * count


RPC_METHODS: Mapping[str, Callable[..., object]] = MappingProxyType(
    {
        "add": add,
        "repeat": repeat,
    }
)


@dataclass(frozen=True)
class RpcRequest:
    """One immutable allowlisted RPC request."""

    request_id: int
    method: str
    args: tuple[object, ...]
    kwargs: tuple[tuple[str, object], ...]


@dataclass(frozen=True)
class RpcSuccess:
    """Successful identified RPC reply."""

    request_id: int
    value: object


@dataclass(frozen=True)
class RpcFailure:
    """Serializable identified RPC failure."""

    request_id: int
    failure_kind: str
    error_type: str
    message: str


@dataclass(frozen=True)
class StopRequest:
    """Cooperative request for one RPC worker to stop."""


class UnknownMethodError(RuntimeError):
    """Raised when a method name is outside ``RPC_METHODS``."""


class RemoteCallError(RuntimeError):
    """Raised when an allowlisted method fails in a worker."""


class _QueueLike(Protocol):
    def put(self, value: object) -> None: ...

    def get(self, timeout: float | None = None) -> object: ...


class _ClosableQueue(_QueueLike, Protocol):
    def cancel_join_thread(self) -> None: ...

    def close(self) -> None: ...

    def join_thread(self) -> None: ...


class _ProcessHandle(Protocol):
    pid: int | None

    @property
    def exitcode(self) -> int | None: ...

    def start(self) -> None: ...

    def join(self, timeout: float | None = None) -> None: ...

    def is_alive(self) -> bool: ...

    def terminate(self) -> None: ...


class _ProcessContext(Protocol):
    def Queue(self) -> _ClosableQueue: ...

    def Process(
        self,
        *,
        target: Callable[..., None],
        args: tuple[object, ...],
        name: str,
    ) -> _ProcessHandle: ...


def _validated_worker_count(worker_count: int) -> int:
    if type(worker_count) is not int:
        raise TypeError("worker_count must be an integer")
    if worker_count < 1:
        raise ValueError("worker_count must be positive")
    return worker_count


def _validated_timeout(timeout: float) -> float:
    raw_timeout: object = cast(object, timeout)
    if isinstance(raw_timeout, bool) or not isinstance(raw_timeout, (int, float)):
        raise TypeError("timeout must be a number")
    value: float = float(raw_timeout)
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("timeout must be positive")
    return value


def _rpc_worker(requests: _QueueLike, replies: _QueueLike) -> None:
    while True:
        raw_request: object = requests.get()
        if isinstance(raw_request, StopRequest):
            return
        if not isinstance(raw_request, RpcRequest):
            raise TypeError("invalid RPC request")

        method: Callable[..., object] | None = RPC_METHODS.get(raw_request.method)
        if method is None:
            reply: RpcSuccess | RpcFailure = RpcFailure(
                raw_request.request_id,
                "unknown_method",
                "UnknownMethodError",
                f"unknown RPC method: {raw_request.method}",
            )
        else:
            try:
                value: object = method(
                    *raw_request.args,
                    **dict(raw_request.kwargs),
                )
            except Exception as error:
                reply = RpcFailure(
                    raw_request.request_id,
                    "remote_call",
                    type(error).__name__,
                    str(error),
                )
            else:
                reply = RpcSuccess(raw_request.request_id, value)
        replies.put(reply)


class RpcWorkerPool:
    """Persistent spawn workers serving only immutable ``RPC_METHODS``."""

    def __init__(
        self,
        *,
        worker_count: int = 2,
        context: BaseContext | None = None,
        shutdown_timeout: float = 5.0,
    ) -> None:
        workers: int = _validated_worker_count(worker_count)
        self._shutdown_timeout: float = _validated_timeout(shutdown_timeout)
        runtime_context: BaseContext = (
            context if context is not None else multiprocessing.get_context("spawn")
        )
        typed_context: _ProcessContext = cast(_ProcessContext, runtime_context)
        self._requests: _ClosableQueue = typed_context.Queue()
        self._replies: _ClosableQueue = typed_context.Queue()
        self._workers: tuple[_ProcessHandle, ...] = tuple(
            typed_context.Process(
                target=_rpc_worker,
                args=(self._requests, self._replies),
                name=f"rpc-worker-{index}",
            )
            for index in range(workers)
        )
        self._next_request_id: int = 0
        self._cache: dict[int, RpcSuccess | RpcFailure] = {}
        self._closed: bool = False
        process: _ProcessHandle
        for process in self._workers:
            process.start()

    @property
    def worker_pids(self) -> tuple[int, ...]:
        """Return stable worker identifiers."""

        pids: list[int] = []
        process: _ProcessHandle
        for process in self._workers:
            if process.pid is None:
                raise RuntimeError("worker has not started")
            pids.append(process.pid)
        return tuple(pids)

    def call(
        self,
        method: str,
        *args: object,
        timeout: float = 5.0,
        **kwargs: object,
    ) -> object:
        """Invoke one allowlisted method and return its remote value."""

        if self._closed:
            raise RuntimeError("RPC pool is closed")
        raw_method: object = cast(object, method)
        if not isinstance(raw_method, str):
            raise TypeError("method must be a string")
        wait_timeout: float = _validated_timeout(timeout)
        request_id: int = self._next_request_id
        self._next_request_id += 1
        request: RpcRequest = RpcRequest(
            request_id,
            raw_method,
            tuple(args),
            tuple(sorted(kwargs.items())),
        )
        self._requests.put(request)

        deadline: float = monotonic() + wait_timeout
        while request_id not in self._cache:
            remaining: float = deadline - monotonic()
            if remaining <= 0.0:
                raise TimeoutError(f"RPC request {request_id} timed out")
            try:
                raw_reply: object = self._replies.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError(f"RPC request {request_id} timed out") from None
            if not isinstance(raw_reply, (RpcSuccess, RpcFailure)):
                raise RuntimeError("worker returned an invalid RPC reply")
            self._cache[raw_reply.request_id] = raw_reply

        reply: RpcSuccess | RpcFailure = self._cache.pop(request_id)
        if isinstance(reply, RpcSuccess):
            return reply.value
        detail: str = f"request {request_id}: {reply.error_type}: {reply.message}"
        if reply.failure_kind == "unknown_method":
            raise UnknownMethodError(detail)
        raise RemoteCallError(detail)

    def close(self) -> None:
        """Cooperatively stop RPC workers with bounded failure cleanup."""

        if self._closed:
            return
        self._closed = True
        for _ in self._workers:
            self._requests.put(StopRequest())

        deadline: float = monotonic() + self._shutdown_timeout
        process: _ProcessHandle
        for process in self._workers:
            process.join(max(0.0, deadline - monotonic()))
        alive: list[_ProcessHandle] = [
            process for process in self._workers if process.is_alive()
        ]
        cleanup_error: BaseException | None = None
        if alive:
            cleanup_error = TimeoutError("RPC worker shutdown timed out")
            for process in alive:
                process.terminate()
            for process in alive:
                process.join(self._shutdown_timeout)
        elif any(process.exitcode != 0 for process in self._workers):
            exitcodes: tuple[int | None, ...] = tuple(
                process.exitcode for process in self._workers
            )
            cleanup_error = ChildProcessError(
                f"RPC workers exited unsuccessfully: {exitcodes}"
            )

        if cleanup_error is not None:
            self._requests.cancel_join_thread()
            self._replies.cancel_join_thread()
        self._requests.close()
        self._replies.close()
        if cleanup_error is None:
            self._requests.join_thread()
            self._replies.join_thread()
        if cleanup_error is not None:
            raise cleanup_error

    def __enter__(self) -> RpcWorkerPool:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        try:
            self.close()
        except BaseException:
            if exception_type is None:
                raise
        return None


def main() -> None:
    """Run a bounded allowlisted RPC demonstration."""

    with RpcWorkerPool(worker_count=2) as rpc:
        print(rpc.call("add", 20, 22, timeout=5.0))
        print(rpc.call("repeat", "rpc", count=2, timeout=5.0))


if __name__ == "__main__":
    main()
