"""Recursive file-size scheduling with persistent thread or process workers."""

from __future__ import annotations

import math
import multiprocessing
import queue
import stat
import threading
from collections.abc import Callable
from dataclasses import dataclass
from multiprocessing.context import BaseContext
from os import stat_result
from pathlib import Path
from time import monotonic
from typing import Protocol, cast

__all__: list[str] = [
    "ScanFailure",
    "ScanResult",
    "WorkerScanError",
    "multiprocessing_recursive_size",
    "threaded_recursive_size",
]

PATH: Path = Path(__file__).parent
_ScanMessage = "ScanResult | ScanFailure"


@dataclass(frozen=True)
class ScanResult:
    """Successful scan of one queued directory."""

    directory: Path
    child_directories: tuple[Path, ...]
    byte_count: int


@dataclass(frozen=True)
class ScanFailure:
    """Serializable worker failure for one queued directory."""

    directory: Path
    error_type: str
    message: str


class WorkerScanError(RuntimeError):
    """Raised when recursive workers cannot scan queued directories."""

    def __init__(
        self,
        failure: ScanFailure | tuple[ScanFailure, ...],
    ) -> None:
        failures: tuple[ScanFailure, ...] = (
            (failure,) if isinstance(failure, ScanFailure) else failure
        )
        if not failures:
            raise ValueError("at least one scan failure is required")
        self.failures: tuple[ScanFailure, ...] = tuple(
            sorted(failures, key=lambda item: str(item.directory))
        )
        self.failure: ScanFailure = self.failures[0]
        details: str = "; ".join(
            f"{item.directory}: {item.error_type}: {item.message}"
            for item in self.failures
        )
        super().__init__(details)


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
        target: Callable[[_QueueLike, _QueueLike], None],
        args: tuple[_QueueLike, _QueueLike],
        name: str,
    ) -> _ProcessHandle: ...


def _validated_directory(directory: Path) -> Path:
    if directory.is_symlink() or not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a directory")
    return directory


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


def _remaining(deadline: float) -> float:
    remaining: float = deadline - monotonic()
    if remaining <= 0.0:
        raise TimeoutError("recursive scan timed out")
    return remaining


def _scan_directory(directory: Path) -> ScanResult:
    metadata: stat_result = directory.lstat()
    if not stat.S_ISDIR(metadata.st_mode):
        raise NotADirectoryError(f"{directory} is not a directory")

    children: list[Path] = []
    byte_count: int = 0
    child: Path
    for child in sorted(directory.iterdir(), key=lambda path: path.name):
        try:
            child_metadata: stat_result = child.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISDIR(child_metadata.st_mode):
            children.append(child)
        elif stat.S_ISREG(child_metadata.st_mode):
            byte_count += child_metadata.st_size
    return ScanResult(directory, tuple(children), byte_count)


def _failure(directory: Path, error: Exception) -> ScanFailure:
    return ScanFailure(directory, type(error).__name__, str(error))


def _thread_worker(
    tasks: queue.Queue[Path | None],
    results: queue.Queue[ScanResult | ScanFailure],
    stop: threading.Event,
) -> None:
    while True:
        directory: Path | None = tasks.get()
        if directory is None or stop.is_set():
            return
        try:
            result: ScanResult | ScanFailure = _scan_directory(directory)
        except Exception as error:
            result = _failure(directory, error)
        results.put(result)


def _process_worker(tasks: _QueueLike, results: _QueueLike) -> None:
    while True:
        raw_directory: object = tasks.get()
        if raw_directory is None:
            return
        if not isinstance(raw_directory, Path):
            raise TypeError("invalid scan task")
        try:
            result: ScanResult | ScanFailure = _scan_directory(raw_directory)
        except Exception as error:
            result = _failure(raw_directory, error)
        results.put(result)


def _schedule(
    directory: Path,
    tasks: _QueueLike,
    results: _QueueLike,
    timeout: float,
) -> int:
    deadline: float = monotonic() + timeout
    outstanding: int = 1
    total: int = 0
    failures: list[ScanFailure] = []
    tasks.put(directory)
    while outstanding:
        try:
            raw_result: object = results.get(timeout=_remaining(deadline))
        except queue.Empty:
            raise TimeoutError("recursive scan timed out") from None
        outstanding -= 1
        if isinstance(raw_result, ScanFailure):
            failures.append(raw_result)
            continue
        if not isinstance(raw_result, ScanResult):
            raise RuntimeError("worker returned an invalid scan message")
        total += raw_result.byte_count
        child: Path
        for child in raw_result.child_directories:
            tasks.put(child)
            outstanding += 1
    if failures:
        raise WorkerScanError(tuple(failures))
    return total


def threaded_recursive_size(
    directory: Path,
    *,
    worker_count: int = 4,
    timeout: float = 5.0,
) -> int:
    """Traverse recursively with persistent raw-thread workers."""

    path: Path = _validated_directory(directory)
    workers: int = _validated_worker_count(worker_count)
    wait_timeout: float = _validated_timeout(timeout)
    tasks: queue.Queue[Path | None] = queue.Queue()
    results: queue.Queue[ScanResult | ScanFailure] = queue.Queue()
    stop: threading.Event = threading.Event()
    threads: list[threading.Thread] = [
        threading.Thread(
            target=_thread_worker,
            args=(tasks, results, stop),
            name=f"recursive-scan-{index}",
            daemon=True,
        )
        for index in range(workers)
    ]
    thread: threading.Thread
    for thread in threads:
        thread.start()

    total: int = 0
    operation_error: BaseException | None = None
    try:
        total = _schedule(
            path, cast(_QueueLike, tasks), cast(_QueueLike, results), wait_timeout
        )
    except BaseException as error:
        operation_error = error

    stop.set()
    for _ in threads:
        tasks.put(None)
    cleanup_deadline: float = monotonic() + wait_timeout
    for thread in threads:
        remaining: float = max(0.0, cleanup_deadline - monotonic())
        thread.join(remaining)
    cleanup_error: TimeoutError | None = None
    if any(thread.is_alive() for thread in threads):
        cleanup_error = TimeoutError("thread workers did not stop")

    if operation_error is not None:
        raise operation_error
    if cleanup_error is not None:
        raise cleanup_error
    return total


def multiprocessing_recursive_size(
    directory: Path,
    *,
    worker_count: int = 2,
    timeout: float = 5.0,
    context: BaseContext | None = None,
) -> int:
    """Traverse recursively with persistent spawn-process workers."""

    path: Path = _validated_directory(directory)
    workers: int = _validated_worker_count(worker_count)
    wait_timeout: float = _validated_timeout(timeout)
    process_context: BaseContext = (
        context if context is not None else multiprocessing.get_context("spawn")
    )
    typed_context: _ProcessContext = cast(_ProcessContext, process_context)
    tasks: _ClosableQueue = typed_context.Queue()
    results: _ClosableQueue = typed_context.Queue()
    processes: list[_ProcessHandle] = [
        typed_context.Process(
            target=_process_worker,
            args=(tasks, results),
            name=f"recursive-scan-{index}",
        )
        for index in range(workers)
    ]
    process: _ProcessHandle
    for process in processes:
        process.start()

    total: int = 0
    operation_error: BaseException | None = None
    try:
        total = _schedule(path, tasks, results, wait_timeout)
    except BaseException as error:
        operation_error = error

    for _ in processes:
        tasks.put(None)
    cleanup_deadline: float = monotonic() + wait_timeout
    for process in processes:
        remaining: float = max(0.0, cleanup_deadline - monotonic())
        process.join(remaining)

    cleanup_error: BaseException | None = None
    alive: list[_ProcessHandle] = [
        process for process in processes if process.is_alive()
    ]
    if alive:
        cleanup_error = TimeoutError("process workers did not stop")
        for process in alive:
            process.terminate()
        for process in alive:
            process.join(wait_timeout)
    elif any(process.exitcode != 0 for process in processes):
        exitcodes: tuple[int | None, ...] = tuple(
            process.exitcode for process in processes
        )
        cleanup_error = ChildProcessError(
            f"recursive workers exited unsuccessfully: {exitcodes}"
        )

    if cleanup_error is not None:
        tasks.cancel_join_thread()
        results.cancel_join_thread()
    tasks.close()
    results.close()
    if cleanup_error is None:
        tasks.join_thread()
        results.join_thread()

    if operation_error is not None:
        raise operation_error
    if cleanup_error is not None:
        raise cleanup_error
    return total


def main(path: Path = PATH) -> None:
    """Print bounded thread and process recursive totals."""

    thread_total: int = threaded_recursive_size(path, worker_count=2)
    process_total: int = multiprocessing_recursive_size(path, worker_count=2)
    print(f"Threaded recursive size for {path} is: {thread_total}")
    print(f"Process recursive size for {path} is: {process_total}")


if __name__ == "__main__":
    main()
