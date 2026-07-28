"""Generic persistent multiprocessing workers over typed queue messages."""

from __future__ import annotations

import math
import multiprocessing
import queue
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from multiprocessing.context import BaseContext
from time import monotonic
from types import TracebackType
from typing import Generic, Protocol, TypeVar, cast

__all__: list[str] = [
    "Failure",
    "PersistentWorkerPool",
    "Success",
    "Task",
    "WorkerError",
    "square",
]

InputT = TypeVar("InputT")
ResultT = TypeVar("ResultT")


@dataclass(frozen=True)
class Task(Generic[InputT]):
    """One identified input queued for a persistent worker."""

    task_id: int
    value: InputT


@dataclass(frozen=True)
class Success(Generic[ResultT]):
    """Successful identified worker reply."""

    task_id: int
    value: ResultT


@dataclass(frozen=True)
class Failure:
    """Serializable identified worker failure."""

    task_id: int
    error_type: str
    message: str


class WorkerError(RuntimeError):
    """Raised when a task fails inside a worker process."""

    def __init__(self, failure: Failure) -> None:
        super().__init__(
            f"task {failure.task_id}: {failure.error_type}: {failure.message}"
        )
        self.failure: Failure = failure


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


def _worker_main(
    function: Callable[[object], object],
    tasks: _QueueLike,
    replies: _QueueLike,
) -> None:
    while True:
        raw_task: object = tasks.get()
        if raw_task is None:
            return
        if not isinstance(raw_task, Task):
            raise TypeError("invalid worker task")
        task: Task[object] = cast(Task[object], raw_task)
        try:
            value: object = function(task.value)
        except Exception as error:
            reply: Success[object] | Failure = Failure(
                task.task_id,
                type(error).__name__,
                str(error),
            )
        else:
            reply = Success(task.task_id, value)
        replies.put(reply)


class PersistentWorkerPool(Generic[InputT, ResultT]):
    """Persistent spawn workers serving one picklable function."""

    def __init__(
        self,
        function: Callable[[InputT], ResultT],
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
        self._tasks: _ClosableQueue = typed_context.Queue()
        self._replies: _ClosableQueue = typed_context.Queue()
        worker_function: Callable[[object], object] = cast(
            Callable[[object], object],
            function,
        )
        self._workers: tuple[_ProcessHandle, ...] = tuple(
            typed_context.Process(
                target=_worker_main,
                args=(worker_function, self._tasks, self._replies),
                name=f"persistent-worker-{index}",
            )
            for index in range(workers)
        )
        self._next_task_id: int = 0
        self._submitted: set[int] = set()
        self._cache: dict[int, Success[object] | Failure] = {}
        self._closed: bool = False
        process: _ProcessHandle
        for process in self._workers:
            process.start()

    @property
    def workers(self) -> tuple[_ProcessHandle, ...]:
        """Return worker handles for lifecycle inspection."""

        return self._workers

    @property
    def worker_pids(self) -> tuple[int, ...]:
        """Return stable started worker process identifiers."""

        pids: list[int] = []
        process: _ProcessHandle
        for process in self._workers:
            if process.pid is None:
                raise RuntimeError("worker has not started")
            pids.append(process.pid)
        return tuple(pids)

    def submit(self, value: InputT) -> int:
        """Queue one value and return its monotonic task identifier."""

        if self._closed:
            raise RuntimeError("pool is closed")
        task_id: int = self._next_task_id
        self._next_task_id += 1
        self._submitted.add(task_id)
        self._tasks.put(Task(task_id, value))
        return task_id

    def result(self, task_id: int, *, timeout: float = 5.0) -> ResultT:
        """Return one result, caching replies that arrive out of order."""

        wait_timeout: float = _validated_timeout(timeout)
        if task_id not in self._submitted:
            raise KeyError(f"unknown task identifier: {task_id}")
        deadline: float = monotonic() + wait_timeout
        while task_id not in self._cache:
            remaining: float = deadline - monotonic()
            if remaining <= 0.0:
                raise TimeoutError(f"task {task_id} timed out")
            try:
                raw_reply: object = self._replies.get(timeout=remaining)
            except queue.Empty:
                raise TimeoutError(f"task {task_id} timed out") from None
            if not isinstance(raw_reply, (Success, Failure)):
                raise RuntimeError("worker returned an invalid reply")
            self._cache[raw_reply.task_id] = raw_reply

        reply: Success[object] | Failure = self._cache.pop(task_id)
        self._submitted.remove(task_id)
        if isinstance(reply, Failure):
            raise WorkerError(reply)
        return cast(ResultT, reply.value)

    def map(
        self,
        values: Iterable[InputT],
        *,
        timeout: float = 5.0,
    ) -> list[ResultT]:
        """Return results in input order using the persistent workers."""

        wait_timeout: float = _validated_timeout(timeout)
        task_ids: list[int] = [self.submit(value) for value in values]
        deadline: float = monotonic() + wait_timeout
        results: list[ResultT] = []
        task_id: int
        for task_id in task_ids:
            remaining: float = deadline - monotonic()
            if remaining <= 0.0:
                raise TimeoutError("worker map timed out")
            results.append(self.result(task_id, timeout=remaining))
        return results

    def close(self) -> None:
        """Cooperatively stop workers; force cleanup only after timeout."""

        if self._closed:
            return
        self._closed = True
        for _ in self._workers:
            self._tasks.put(None)

        deadline: float = monotonic() + self._shutdown_timeout
        process: _ProcessHandle
        for process in self._workers:
            process.join(max(0.0, deadline - monotonic()))
        alive: list[_ProcessHandle] = [
            process for process in self._workers if process.is_alive()
        ]
        cleanup_error: BaseException | None = None
        if alive:
            cleanup_error = TimeoutError("worker pool shutdown timed out")
            for process in alive:
                process.terminate()
            for process in alive:
                process.join(self._shutdown_timeout)
        elif any(process.exitcode != 0 for process in self._workers):
            exitcodes: tuple[int | None, ...] = tuple(
                process.exitcode for process in self._workers
            )
            cleanup_error = ChildProcessError(
                f"workers exited unsuccessfully: {exitcodes}"
            )

        if cleanup_error is not None:
            self._tasks.cancel_join_thread()
            self._replies.cancel_join_thread()
        self._tasks.close()
        self._replies.close()
        if cleanup_error is None:
            self._tasks.join_thread()
            self._replies.join_thread()
        if cleanup_error is not None:
            raise cleanup_error

    def __enter__(self) -> PersistentWorkerPool[InputT, ResultT]:
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


def square(value: int) -> int:
    """Return ``value`` squared; top-level for spawn pickling."""

    return value * value


def main() -> None:
    """Run a bounded spawn-safe persistent-worker demonstration."""

    with PersistentWorkerPool(square, worker_count=2) as pool:
        print(pool.map([1, 2, 3, 4], timeout=5.0))


if __name__ == "__main__":
    main()
