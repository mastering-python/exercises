"""Deterministic threaded file-size aggregation without symlink traversal."""

from __future__ import annotations

import errno
import os
import stat
from concurrent.futures import Future, ThreadPoolExecutor
from os import PathLike, stat_result
from pathlib import Path
from typing import cast

__all__: list[str] = [
    "get_size",
    "get_total_size",
    "get_total_size_recursive",
    "main",
]

PATH: Path = Path(__file__).parent
_DIRECTORY_OPEN_FLAGS: int = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
_REPLACED_DIRECTORY_ERRORS: frozenset[int] = frozenset(
    {errno.ENOENT, errno.ENOTDIR, errno.ELOOP}
)
_DEFAULT_PENDING_SIZES: int = min(32, (os.cpu_count() or 1) + 4)


class _DescriptorPath:
    """Path display plus descriptor-relative metadata access."""

    def __init__(self, path: Path, directory_fd: int, entry_name: str) -> None:
        self._path: Path = path
        self._directory_fd: int = directory_fd
        self._entry_name: str = entry_name

    @property
    def name(self) -> str:
        return self._path.name

    def as_posix(self) -> str:
        return self._path.as_posix()

    def lstat(self) -> stat_result:
        return os.stat(
            self._entry_name,
            dir_fd=self._directory_fd,
            follow_symlinks=False,
        )

    def relative_to(self, other: str | PathLike[str]) -> Path:
        return self._path.relative_to(other)

    def symlink_to(
        self,
        target: str | PathLike[str],
        target_is_directory: bool = False,
    ) -> None:
        self._path.symlink_to(target, target_is_directory=target_is_directory)

    def unlink(self, missing_ok: bool = False) -> None:
        self._path.unlink(missing_ok=missing_ok)

    def __fspath__(self) -> str:
        return os.fspath(self._path)

    def __str__(self) -> str:
        return str(self._path)


class _PendingSize:
    """One worker future and the descriptor it owns."""

    def __init__(
        self,
        future: Future[int],
        directory_fd: int | None,
    ) -> None:
        self.future: Future[int] = future
        self.directory_fd: int | None = directory_fd


class _SizeCollector:
    """Bound submitted size work and close descriptors as results settle."""

    def __init__(self, executor: ThreadPoolExecutor, pending_limit: int) -> None:
        self._executor: ThreadPoolExecutor = executor
        self._pending_limit: int = pending_limit
        self._pending: dict[int, _PendingSize] = {}
        self._next_identifier: int = 0
        self.total: int = 0

    def submit(
        self,
        path: Path,
        directory_fd: int | None,
    ) -> None:
        try:
            if len(self._pending) >= self._pending_limit:
                oldest_identifier: int = next(iter(self._pending))
                self._settle(oldest_identifier)

            identifier: int = self._next_identifier
            self._next_identifier += 1
            future: Future[int] = self._executor.submit(get_size, path)
            self._pending[identifier] = _PendingSize(future, directory_fd)
        except BaseException:
            if directory_fd is not None:
                os.close(directory_fd)
            raise

    def settle_all(self, *, suppress_errors: bool = False) -> None:
        first_error: BaseException | None = None
        while self._pending:
            oldest_identifier: int = next(iter(self._pending))
            try:
                self._settle(oldest_identifier)
            except BaseException as error:
                if first_error is None:
                    first_error = error

        if first_error is not None and not suppress_errors:
            raise first_error

    def _settle(self, identifier: int) -> None:
        pending: _PendingSize = self._pending.pop(identifier)
        try:
            self.total += pending.future.result()
        finally:
            if pending.directory_fd is not None:
                os.close(pending.directory_fd)


class _TraversalWork:
    """One root-relative file or directory queued for depth-first work."""

    def __init__(
        self,
        components: tuple[str, ...],
        *,
        is_directory: bool,
    ) -> None:
        self.components: tuple[str, ...] = components
        self.is_directory: bool = is_directory


def get_size(path: Path) -> int:
    """Return the size of one regular file."""

    try:
        metadata: stat_result = path.lstat()
    except FileNotFoundError:
        raise FileNotFoundError(f"not a regular file: {path}") from None
    if not stat.S_ISREG(metadata.st_mode):
        raise FileNotFoundError(f"not a regular file: {path}")
    return metadata.st_size


def _validated_directory(path: Path) -> Path:
    if path.is_symlink() or not path.is_dir():
        raise NotADirectoryError(f"{path} is not a directory")
    return path


def _validated_max_workers(max_workers: int | None) -> int | None:
    if max_workers is None:
        return None
    if type(max_workers) is not int:
        raise TypeError("max_workers must be an integer")
    if max_workers <= 0:
        raise ValueError("max_workers must be positive")
    return max_workers


def _open_root_directory(path: Path) -> int:
    try:
        return os.open(path, _DIRECTORY_OPEN_FLAGS)
    except OSError as error:
        if error.errno in _REPLACED_DIRECTORY_ERRORS:
            raise NotADirectoryError(f"{path} is not a directory") from None
        raise


def _descriptor_path(path: Path, directory_fd: int, entry_name: str) -> Path:
    descriptor_path: _DescriptorPath = _DescriptorPath(
        path,
        directory_fd,
        entry_name,
    )
    return cast(Path, descriptor_path)


def _open_child_directory(entry_name: str, parent_fd: int) -> int | None:
    try:
        return os.open(
            entry_name,
            _DIRECTORY_OPEN_FLAGS,
            dir_fd=parent_fd,
        )
    except OSError as error:
        if error.errno in _REPLACED_DIRECTORY_ERRORS:
            return None
        raise


def _open_relative_directory(
    root_fd: int,
    components: tuple[str, ...],
) -> tuple[int, bool] | None:
    current_fd: int = root_fd
    current_is_owned: bool = False
    component: str
    for component in components:
        try:
            child_fd: int | None = _open_child_directory(component, current_fd)
        except BaseException:
            if current_is_owned:
                os.close(current_fd)
            raise
        if child_fd is None:
            if current_is_owned:
                os.close(current_fd)
            return None
        if current_is_owned:
            try:
                os.close(current_fd)
            except BaseException:
                os.close(child_fd)
                raise
        current_fd = child_fd
        current_is_owned = True
    return current_fd, current_is_owned


def _discover_relative_directory(
    root_fd: int,
    components: tuple[str, ...],
) -> list[_TraversalWork]:
    opened: tuple[int, bool] | None = _open_relative_directory(root_fd, components)
    if opened is None:
        return []
    directory_fd, directory_is_owned = opened
    try:
        work: list[_TraversalWork] = []
        entry_name: str
        for entry_name in sorted(os.listdir(directory_fd)):
            try:
                metadata: stat_result = os.stat(
                    entry_name,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                continue
            child_components: tuple[str, ...] = (*components, entry_name)
            if stat.S_ISDIR(metadata.st_mode):
                work.append(
                    _TraversalWork(
                        child_components,
                        is_directory=True,
                    )
                )
            elif stat.S_ISREG(metadata.st_mode):
                work.append(
                    _TraversalWork(
                        child_components,
                        is_directory=False,
                    )
                )
        return work
    finally:
        if directory_is_owned:
            os.close(directory_fd)


def _submit_relative_file(
    root_fd: int,
    root_path: Path,
    components: tuple[str, ...],
    collector: _SizeCollector,
) -> None:
    parent_components: tuple[str, ...] = components[:-1]
    entry_name: str = components[-1]
    opened: tuple[int, bool] | None = _open_relative_directory(
        root_fd,
        parent_components,
    )
    if opened is None:
        return
    directory_fd, directory_is_owned = opened
    descriptor_was_transferred: bool = False
    try:
        try:
            metadata: stat_result = os.stat(
                entry_name,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            return
        if not stat.S_ISREG(metadata.st_mode):
            return

        display_path: Path = root_path.joinpath(*components)
        descriptor_path: Path = _descriptor_path(
            display_path,
            directory_fd,
            entry_name,
        )
        owned_fd: int | None = directory_fd if directory_is_owned else None
        descriptor_was_transferred = directory_is_owned
        collector.submit(descriptor_path, owned_fd)
    finally:
        if directory_is_owned and not descriptor_was_transferred:
            os.close(directory_fd)


def _collect_recursive_tree(
    root_fd: int,
    path: Path,
    collector: _SizeCollector,
) -> None:
    pending: list[_TraversalWork] = [_TraversalWork((), is_directory=True)]
    try:
        while pending:
            work: _TraversalWork = pending.pop()
            if work.is_directory:
                children: list[_TraversalWork] = _discover_relative_directory(
                    root_fd,
                    work.components,
                )
                pending.extend(reversed(children))
            else:
                _submit_relative_file(
                    root_fd,
                    path,
                    work.components,
                    collector,
                )
        collector.settle_all()
    except BaseException:
        collector.settle_all(suppress_errors=True)
        raise
    finally:
        os.close(root_fd)


def _pending_size_limit(max_workers: int | None) -> int:
    if max_workers is None:
        return _DEFAULT_PENDING_SIZES
    return max_workers


def _total_size_flat(path: Path, max_workers: int | None) -> int:
    pending_limit: int = _pending_size_limit(max_workers)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        collector: _SizeCollector = _SizeCollector(executor, pending_limit)
        root_fd: int = _open_root_directory(path)
        try:
            entry_name: str
            for entry_name in sorted(os.listdir(root_fd)):
                try:
                    metadata: stat_result = os.stat(
                        entry_name,
                        dir_fd=root_fd,
                        follow_symlinks=False,
                    )
                except FileNotFoundError:
                    continue
                if stat.S_ISREG(metadata.st_mode):
                    descriptor_path: Path = _descriptor_path(
                        path / entry_name,
                        root_fd,
                        entry_name,
                    )
                    collector.submit(descriptor_path, None)
            collector.settle_all()
        except BaseException:
            collector.settle_all(suppress_errors=True)
            raise
        finally:
            os.close(root_fd)
        return collector.total


def _total_size_recursive(path: Path, max_workers: int | None) -> int:
    pending_limit: int = _pending_size_limit(max_workers)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        collector: _SizeCollector = _SizeCollector(executor, pending_limit)
        root_fd: int = _open_root_directory(path)
        _collect_recursive_tree(root_fd, path, collector)
        return collector.total


def get_total_size(
    path: Path,
    *,
    max_workers: int | None = None,
) -> int:
    """Sum immediate non-symlink regular files in ``path``."""

    directory: Path = _validated_directory(path)
    workers: int | None = _validated_max_workers(max_workers)
    return _total_size_flat(directory, workers)


def get_total_size_recursive(
    path: Path,
    *,
    max_workers: int | None = None,
) -> int:
    """Sum nested non-symlink regular files without following symlinks."""

    directory: Path = _validated_directory(path)
    workers: int | None = _validated_max_workers(max_workers)
    return _total_size_recursive(directory, workers)


def main(
    path: Path,
    *,
    max_workers: int | None = None,
) -> None:
    """Print flat and recursive totals for ``path``."""

    total_size: int = get_total_size(path, max_workers=max_workers)
    print(f"Total size for {path} is: {total_size}")
    recursive_size: int = get_total_size_recursive(
        path,
        max_workers=max_workers,
    )
    print(f"Recursive total size for {path} is: {recursive_size}")


if __name__ == "__main__":
    main(PATH)
