"""Immediate file-size totals with persistent threads or spawn processes."""

from __future__ import annotations

import multiprocessing
import queue
import stat
import threading
from collections.abc import Callable
from multiprocessing.context import BaseContext
from os import stat_result
from pathlib import Path
from types import TracebackType
from typing import Protocol, cast

__all__: list[str] = [
    "multiprocessing_total_size",
    "threaded_total_size",
]

PATH: Path = Path(__file__).parent
_ThreadTask = tuple[int, Path] | None


class _ProcessPool(Protocol):
    def __enter__(self) -> _ProcessPool: ...

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None: ...

    def map(
        self,
        function: Callable[[Path], int],
        values: list[Path],
    ) -> list[int]: ...


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


def _immediate_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    child: Path
    for child in sorted(directory.iterdir(), key=lambda path: path.name):
        try:
            metadata: stat_result = child.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISREG(metadata.st_mode):
            files.append(child)
    return files


def _stat_size(path: Path) -> int:
    metadata: stat_result = path.lstat()
    if not stat.S_ISREG(metadata.st_mode):
        raise FileNotFoundError(f"not a regular file: {path}")
    return metadata.st_size


def threaded_total_size(
    directory: Path,
    *,
    worker_count: int = 4,
) -> int:
    """Return the total size of immediate files using raw persistent threads."""

    path: Path = _validated_directory(directory)
    workers: int = _validated_worker_count(worker_count)
    files: list[Path] = _immediate_files(path)
    if not files:
        return 0

    task_queue: queue.Queue[_ThreadTask] = queue.Queue()
    results: dict[int, int] = {}
    failures: dict[int, Exception] = {}
    result_lock: threading.Lock = threading.Lock()

    def worker() -> None:
        while True:
            task: _ThreadTask = task_queue.get()
            try:
                if task is None:
                    return
                task_id, file_path = task
                try:
                    size: int = _stat_size(file_path)
                except Exception as error:
                    with result_lock:
                        failures[task_id] = error
                else:
                    with result_lock:
                        results[task_id] = size
            finally:
                task_queue.task_done()

    active_worker_count: int = min(workers, len(files))
    threads: list[threading.Thread] = [
        threading.Thread(target=worker, name=f"file-size-{index}")
        for index in range(active_worker_count)
    ]
    thread: threading.Thread
    for thread in threads:
        thread.start()

    task_id: int
    file_path: Path
    for task_id, file_path in enumerate(files):
        task_queue.put((task_id, file_path))
    task_queue.join()
    for _ in threads:
        task_queue.put(None)
    task_queue.join()
    for thread in threads:
        thread.join()

    if failures:
        raise failures[min(failures)]
    return sum(results[index] for index in range(len(files)))


def multiprocessing_total_size(
    directory: Path,
    *,
    worker_count: int = 2,
    context: BaseContext | None = None,
) -> int:
    """Return the total size of immediate files using a process pool."""

    path: Path = _validated_directory(directory)
    workers: int = _validated_worker_count(worker_count)
    files: list[Path] = _immediate_files(path)
    if not files:
        return 0

    process_context: BaseContext = (
        context if context is not None else multiprocessing.get_context("spawn")
    )
    active_worker_count: int = min(workers, len(files))
    process_pool: _ProcessPool = cast(
        _ProcessPool,
        process_context.Pool(processes=active_worker_count),
    )
    with process_pool as pool:
        sizes: list[int] = pool.map(_stat_size, files)
    return sum(sizes)


def main(path: Path = PATH) -> None:
    """Print bounded thread and process totals for the exercise directory."""

    thread_total: int = threaded_total_size(path, worker_count=2)
    process_total: int = multiprocessing_total_size(path, worker_count=2)
    print(f"Threaded total size for {path} is: {thread_total}")
    print(f"Process total size for {path} is: {process_total}")


if __name__ == "__main__":
    main()
