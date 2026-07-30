"""Tests for deterministic threaded file-size aggregation."""

from __future__ import annotations

import errno
import inspect
import os
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from os import stat_result
from pathlib import Path
from typing import cast, get_type_hints

import pytest

from . import solution_00
from .solution_00 import (
    get_size,
    get_total_size,
    get_total_size_recursive,
    main,
)

SizeFunction = Callable[[Path], int]


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _record_directory_fds(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    original_open: Callable[..., int] = os.open
    opened: list[int] = []

    def recording_open(
        path: object,
        flags: int,
        *args: object,
        **kwargs: object,
    ) -> int:
        descriptor: int = original_open(path, flags, *args, **kwargs)
        if flags & os.O_DIRECTORY:
            opened.append(descriptor)
        return descriptor

    monkeypatch.setattr(os, "open", recording_open)
    return opened


def _assert_descriptors_closed(descriptors: list[int]) -> None:
    descriptor: int
    for descriptor in set(descriptors):
        with pytest.raises(OSError) as error:
            os.fstat(descriptor)
        assert error.value.errno == errno.EBADF


def _assert_recursive_total_with_low_descriptor_limit(
    root: Path,
    expected: int,
) -> None:
    script: str = """
import resource
import sys
from pathlib import Path
from CH_14_multithreading_and_multiprocessing.exercise_02.solution_00 import (
    get_total_size_recursive,
)

original_soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
low_soft = 32 if hard == resource.RLIM_INFINITY else min(32, hard)
if low_soft < 16:
    raise SystemExit(77)
resource.setrlimit(resource.RLIMIT_NOFILE, (low_soft, hard))
try:
    print(get_total_size_recursive(Path(sys.argv[1]), max_workers=2))
finally:
    resource.setrlimit(resource.RLIMIT_NOFILE, (original_soft, hard))
"""
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-c", script, str(root)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 77:
        pytest.skip("RLIMIT_NOFILE hard limit is below the safe test minimum")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == str(expected)


def test_get_size_returns_file_size(tmp_path: Path) -> None:
    path: Path = tmp_path / "value.bin"
    _write(path, b"12345")

    assert get_size(path) == 5


def test_get_size_rejects_non_files(tmp_path: Path) -> None:
    directory: Path = tmp_path / "directory"
    directory.mkdir()
    missing: Path = tmp_path / "missing.bin"

    for path in (directory, missing):
        with pytest.raises(
            FileNotFoundError,
            match=rf"^not a regular file: {path}$",
        ):
            get_size(path)


def test_get_size_rejects_symlink_to_regular_file(tmp_path: Path) -> None:
    target: Path = tmp_path / "target.bin"
    link: Path = tmp_path / "link.bin"
    _write(target, b"contents")
    link.symlink_to(target)

    with pytest.raises(
        FileNotFoundError,
        match=rf"^not a regular file: {link}$",
    ):
        get_size(link)


@pytest.mark.parametrize(
    "function",
    [get_total_size, get_total_size_recursive],
)
def test_worker_rejects_file_replaced_by_symlink_after_discovery(
    function: Callable[..., int],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root: Path = tmp_path / "root"
    outside: Path = tmp_path / "outside.bin"
    discovered: Path = root / "discovered.bin"
    _write(discovered, b"inside")
    _write(outside, b"outside")
    original_get_size: SizeFunction = get_size

    def replace_then_get_size(path: Path) -> int:
        path.unlink()
        path.symlink_to(outside)
        return original_get_size(path)

    monkeypatch.setattr(solution_00, "get_size", replace_then_get_size)

    with pytest.raises(
        FileNotFoundError,
        match=rf"^not a regular file: {discovered}$",
    ):
        function(root, max_workers=1)


def test_recursive_traversal_does_not_follow_directory_replaced_after_stat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root: Path = tmp_path / "root"
    nested: Path = root / "nested"
    outside: Path = tmp_path / "outside"
    _write(root / "root.bin", b"x")
    _write(nested / "removed.bin", b"inside")
    _write(outside / "outside.bin", b"outside-bytes")
    original_stat: Callable[..., stat_result] = os.stat
    replaced: bool = False

    def replace_directory_after_stat(
        path: object,
        *args: object,
        **kwargs: object,
    ) -> stat_result:
        nonlocal replaced
        metadata: stat_result = original_stat(path, *args, **kwargs)
        path_matches: bool = isinstance(path, (str, Path)) and Path(path) == nested
        descriptor_name_matches: bool = (
            path == "nested" and kwargs.get("dir_fd") is not None
        )
        if not replaced and (path_matches or descriptor_name_matches):
            replaced = True
            shutil.rmtree(nested)
            nested.symlink_to(outside, target_is_directory=True)
        return metadata

    monkeypatch.setattr(os, "stat", replace_directory_after_stat)

    assert get_total_size_recursive(root, max_workers=1) == 1
    assert replaced is True


def test_flat_traversal_rejects_root_replaced_after_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root: Path = tmp_path / "root"
    outside: Path = tmp_path / "outside"
    _write(root / "removed.bin", b"inside")
    _write(outside / "outside.bin", b"outside-bytes")
    original_is_dir: Callable[[Path], bool] = Path.is_dir
    replaced: bool = False

    def replace_root_after_validation(path: Path) -> bool:
        nonlocal replaced
        is_directory: bool = original_is_dir(path)
        if not replaced and path == root and is_directory:
            replaced = True
            shutil.rmtree(root)
            root.symlink_to(outside, target_is_directory=True)
        return is_directory

    monkeypatch.setattr(Path, "is_dir", replace_root_after_validation)

    with pytest.raises(NotADirectoryError, match=rf"^{root} is not a directory$"):
        get_total_size(root, max_workers=1)
    assert replaced is True


@pytest.mark.parametrize(
    "function",
    [get_total_size, get_total_size_recursive],
)
def test_aggregator_worker_default_is_none(
    function: Callable[..., int],
    tmp_path: Path,
) -> None:
    _write(tmp_path / "value.bin", b"x")
    parameter: inspect.Parameter = inspect.signature(function).parameters["max_workers"]

    assert parameter.default is None
    assert get_type_hints(function)["max_workers"] == int | None
    assert function(tmp_path) == 1
    assert function(tmp_path, max_workers=None) == 1


def test_flat_total_includes_only_immediate_regular_files(tmp_path: Path) -> None:
    _write(tmp_path / "first.bin", b"12")
    _write(tmp_path / "second.bin", b"345")
    _write(tmp_path / "nested" / "ignored.bin", b"6789")

    assert get_total_size(tmp_path, max_workers=2) == 5


def test_flat_total_bounds_pending_futures_to_worker_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    file_count: int = 24
    index: int
    for index in range(file_count):
        _write(tmp_path / f"value-{index:02d}.bin", b"x")

    original_get_size: SizeFunction = get_size
    original_submit: Callable[..., Future[int]] = cast(
        Callable[..., Future[int]],
        ThreadPoolExecutor.submit,
    )
    original_result: Callable[..., int] = cast(
        Callable[..., int],
        Future[int].result,
    )
    release_workers: threading.Event = threading.Event()
    first_result_started: threading.Event = threading.Event()
    counter_lock: threading.Lock = threading.Lock()
    unresolved: int = 0
    peak_unresolved: int = 0

    def blocking_size(path: Path) -> int:
        release_workers.wait(timeout=5)
        return original_get_size(path)

    def record_submit(
        executor: ThreadPoolExecutor,
        function: Callable[..., int],
        *args: object,
        **kwargs: object,
    ) -> Future[int]:
        nonlocal unresolved, peak_unresolved
        future: Future[int] = original_submit(
            executor,
            function,
            *args,
            **kwargs,
        )
        with counter_lock:
            unresolved += 1
            peak_unresolved = max(peak_unresolved, unresolved)

        def record_completion(completed: Future[int]) -> None:
            nonlocal unresolved
            with counter_lock:
                unresolved -= 1

        future.add_done_callback(record_completion)
        return future

    def record_result(future: Future[int], timeout: float | None = None) -> int:
        first_result_started.set()
        return original_result(future, timeout)

    monkeypatch.setattr(solution_00, "get_size", blocking_size)
    monkeypatch.setattr(ThreadPoolExecutor, "submit", record_submit)
    monkeypatch.setattr(Future, "result", record_result)
    totals: list[int] = []
    errors: list[BaseException] = []

    def calculate_total() -> None:
        try:
            totals.append(get_total_size(tmp_path, max_workers=2))
        except BaseException as error:
            errors.append(error)

    calculation: threading.Thread = threading.Thread(target=calculate_total)
    calculation.start()
    try:
        assert first_result_started.wait(timeout=2)
        with counter_lock:
            assert peak_unresolved <= 2
    finally:
        release_workers.set()
        calculation.join(timeout=5)

    assert calculation.is_alive() is False
    assert errors == []
    assert totals == [file_count]


def test_flat_total_closes_descriptor_after_worker_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(tmp_path / "file.bin", b"value")
    descriptors: list[int] = _record_directory_fds(monkeypatch)

    def fail(path: Path) -> int:
        raise OSError(f"cannot stat {path.name}")

    monkeypatch.setattr(solution_00, "get_size", fail)

    with pytest.raises(OSError, match=r"^cannot stat file\.bin$"):
        get_total_size(tmp_path, max_workers=2)
    assert len(descriptors) == 1
    _assert_descriptors_closed(descriptors)


def test_recursive_total_includes_nested_regular_files(tmp_path: Path) -> None:
    _write(tmp_path / "first.bin", b"12")
    _write(tmp_path / "nested" / "second.bin", b"345")
    _write(tmp_path / "nested" / "deep" / "third.bin", b"6789")

    assert get_total_size_recursive(tmp_path, max_workers=3) == 9


def test_recursive_total_handles_wide_tree_with_low_descriptor_limit(
    tmp_path: Path,
) -> None:
    root: Path = tmp_path / "root"
    expected: int = 0
    index: int
    for index in range(96):
        content: bytes = b"x" * ((index % 7) + 1)
        _write(root / f"directory-{index:03d}" / "value.bin", content)
        expected += len(content)

    _assert_recursive_total_with_low_descriptor_limit(root, expected)


def test_recursive_total_handles_deep_tree_with_low_descriptor_limit(
    tmp_path: Path,
) -> None:
    root: Path = tmp_path / "root"
    directory: Path = root
    depth: int
    for depth in range(96):
        directory /= f"d{depth:02d}"
    _write(directory / "value.bin", b"deep")

    _assert_recursive_total_with_low_descriptor_limit(root, 4)


def test_recursive_total_closes_descriptors_after_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(tmp_path / "root.bin", b"x")
    _write(tmp_path / "nested" / "value.bin", b"yz")
    descriptors: list[int] = _record_directory_fds(monkeypatch)

    assert get_total_size_recursive(tmp_path, max_workers=2) == 3
    assert len(descriptors) >= 2
    _assert_descriptors_closed(descriptors)


def test_recursive_total_closes_descriptors_after_worker_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(tmp_path / "root.bin", b"x")
    _write(tmp_path / "nested" / "value.bin", b"yz")
    descriptors: list[int] = _record_directory_fds(monkeypatch)

    def fail(path: Path) -> int:
        raise OSError(f"cannot stat {path.name}")

    monkeypatch.setattr(solution_00, "get_size", fail)

    with pytest.raises(OSError, match=r"^cannot stat value\.bin$"):
        get_total_size_recursive(tmp_path, max_workers=1)
    assert len(descriptors) >= 2
    _assert_descriptors_closed(descriptors)


def test_empty_directory_has_zero_total(tmp_path: Path) -> None:
    assert get_total_size(tmp_path, max_workers=1) == 0
    assert get_total_size_recursive(tmp_path, max_workers=1) == 0


@pytest.mark.parametrize(
    "function",
    [get_total_size, get_total_size_recursive],
)
def test_root_must_be_directory(
    function: SizeFunction,
    tmp_path: Path,
) -> None:
    file_path: Path = tmp_path / "file.bin"
    _write(file_path, b"value")

    with pytest.raises(
        NotADirectoryError,
        match=rf"^{file_path} is not a directory$",
    ):
        function(file_path)


@pytest.mark.parametrize(
    "function",
    [get_total_size, get_total_size_recursive],
)
@pytest.mark.parametrize("max_workers", [0, -1])
def test_max_workers_must_be_positive(
    function: Callable[..., int],
    max_workers: int,
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match=r"^max_workers must be positive$"):
        function(tmp_path, max_workers=max_workers)


@pytest.mark.parametrize(
    "function",
    [get_total_size, get_total_size_recursive],
)
def test_boolean_max_workers_is_rejected(
    function: Callable[..., int],
    tmp_path: Path,
) -> None:
    with pytest.raises(TypeError, match=r"^max_workers must be an integer$"):
        function(tmp_path, max_workers=cast(int, True))


def test_flat_and_recursive_totals_never_follow_symlinks(tmp_path: Path) -> None:
    root: Path = tmp_path / "root"
    outside: Path = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    _write(root / "real.bin", b"12")
    outside_file: Path = outside / "outside.bin"
    _write(outside_file, b"34567")
    (root / "file-link.bin").symlink_to(outside_file)
    (root / "directory-link").symlink_to(outside, target_is_directory=True)

    assert get_total_size(root, max_workers=2) == 2
    assert get_total_size_recursive(root, max_workers=2) == 2


@pytest.mark.parametrize(
    "function",
    [get_total_size, get_total_size_recursive],
)
def test_symlink_root_is_rejected(
    function: SizeFunction,
    tmp_path: Path,
) -> None:
    real: Path = tmp_path / "real"
    real.mkdir()
    link: Path = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)

    with pytest.raises(NotADirectoryError, match=rf"^{link} is not a directory$"):
        function(link)


def test_discovery_order_is_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(tmp_path / "z.bin", b"z")
    _write(tmp_path / "a.bin", b"a")
    _write(tmp_path / "nested" / "m.bin", b"m")
    seen: list[str] = []

    def record_size(path: Path) -> int:
        seen.append(path.relative_to(tmp_path).as_posix())
        return 1

    monkeypatch.setattr(solution_00, "get_size", record_size)

    assert get_total_size(tmp_path, max_workers=1) == 2
    assert seen == ["a.bin", "z.bin"]

    seen.clear()
    assert get_total_size_recursive(tmp_path, max_workers=1) == 3
    assert seen == ["a.bin", "nested/m.bin", "z.bin"]


@pytest.mark.parametrize(
    "function",
    [get_total_size, get_total_size_recursive],
)
def test_worker_failure_propagates_from_future_result(
    function: Callable[..., int],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write(tmp_path / "file.bin", b"value")

    def fail(path: Path) -> int:
        raise OSError(f"cannot stat {path.name}")

    monkeypatch.setattr(solution_00, "get_size", fail)

    with pytest.raises(OSError, match=r"^cannot stat file\.bin$"):
        function(tmp_path, max_workers=1)


def test_main_reports_flat_and_recursive_totals(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write(tmp_path / "first.bin", b"12")
    _write(tmp_path / "nested" / "second.bin", b"345")

    main(tmp_path, max_workers=1)

    assert capsys.readouterr().out.splitlines() == [
        f"Total size for {tmp_path} is: 2",
        f"Recursive total size for {tmp_path} is: 5",
    ]
