"""Tests executor-backed asynchronous adapters."""

from __future__ import annotations

import asyncio
import concurrent.futures
import inspect
import operator
import socket
import subprocess
import sys
import threading
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any, TypeVar

import pytest

from CH_13_async_io.exercise_02.solution_00 import AsyncExecutor, AsyncioFile

_T = TypeVar("_T")


def _run(coroutine: Coroutine[Any, Any, _T]) -> _T:
    return asyncio.run(coroutine)


def _multiply(left: int, right: int) -> int:
    return left * right


def _raise_lookup_error(message: str) -> None:
    raise LookupError(message)


def test_owned_executor_runs_work_off_the_event_loop_thread() -> None:
    async def scenario() -> None:
        adapter: AsyncExecutor = AsyncExecutor()
        loop_thread: int = threading.get_ident()
        started: threading.Event = threading.Event()
        release: threading.Event = threading.Event()

        def blocking_thread_identity() -> int:
            started.set()
            if not release.wait(timeout=2):
                raise TimeoutError("test did not release worker")
            return threading.get_ident()

        task: asyncio.Task[int] = asyncio.create_task(
            adapter.run(blocking_thread_identity)
        )
        try:
            started_on_time: bool = await asyncio.wait_for(
                asyncio.to_thread(started.wait, 2),
                timeout=3,
            )
            assert started_on_time
            assert not task.done()
            release.set()
            worker_thread: int = await asyncio.wait_for(task, timeout=3)
            assert worker_thread != loop_thread
        finally:
            release.set()
            await adapter.close()

    _run(scenario())


def test_run_returns_results_and_propagates_worker_exceptions() -> None:
    async def scenario() -> None:
        adapter: AsyncExecutor = AsyncExecutor()
        try:
            assert await adapter.run(_multiply, 6, 7) == 42
            with pytest.raises(LookupError, match="worker failed"):
                await adapter.run(_raise_lookup_error, "worker failed")
        finally:
            await adapter.close()

    _run(scenario())


def test_injected_thread_pool_remains_caller_owned() -> None:
    async def scenario(executor: concurrent.futures.ThreadPoolExecutor) -> None:
        adapter: AsyncExecutor = AsyncExecutor(executor)
        assert await adapter.run(_multiply, 3, 9) == 27
        await adapter.close()
        await adapter.close()

        with pytest.raises(RuntimeError, match="closed"):
            await adapter.run(_multiply, 1, 2)

    executor: concurrent.futures.ThreadPoolExecutor = (
        concurrent.futures.ThreadPoolExecutor(max_workers=1)
    )
    try:
        _run(scenario(executor))
        future: concurrent.futures.Future[int] = executor.submit(_multiply, 4, 5)
        assert future.result(timeout=3) == 20
    finally:
        executor.shutdown(wait=True, cancel_futures=True)


def test_injected_process_pool_supports_pickleable_callables() -> None:
    async def scenario(executor: concurrent.futures.ProcessPoolExecutor) -> None:
        adapter: AsyncExecutor = AsyncExecutor(executor)
        assert await asyncio.wait_for(adapter.run(operator.mul, 8, 9), timeout=5) == 72
        await adapter.close()

    executor: concurrent.futures.ProcessPoolExecutor = (
        concurrent.futures.ProcessPoolExecutor(max_workers=1)
    )
    try:
        _run(scenario(executor))
        future: concurrent.futures.Future[int] = executor.submit(operator.mul, 2, 11)
        assert future.result(timeout=5) == 22
    finally:
        executor.shutdown(wait=True, cancel_futures=True)


def test_context_closes_owned_adapter_and_rejects_later_work() -> None:
    async def scenario() -> None:
        adapter: AsyncExecutor = AsyncExecutor()

        entered: AsyncExecutor
        async with adapter as entered:
            assert entered is adapter
            assert not adapter.closed
            assert await adapter.run(_multiply, 2, 3) == 6

        assert adapter.closed
        with pytest.raises(RuntimeError, match="closed"):
            await adapter.run(_multiply, 2, 3)
        await adapter.close()

    _run(scenario())


def test_closed_adapter_rejects_context_entry() -> None:
    async def scenario() -> None:
        adapter: AsyncExecutor = AsyncExecutor()
        await adapter.close()

        with pytest.raises(RuntimeError, match=r"^executor is closed$"):
            async with adapter:
                raise AssertionError("closed adapter entered its context")

    _run(scenario())


def test_owned_executor_shutdown_cancels_pending_futures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        calls: list[tuple[bool, bool]] = []
        adapter: AsyncExecutor = AsyncExecutor()
        owned_executor: object = vars(adapter)["_executor"]
        original_shutdown: Callable[..., None] = (
            concurrent.futures.ThreadPoolExecutor.shutdown
        )

        def recording_shutdown(
            executor: concurrent.futures.ThreadPoolExecutor,
            wait: bool = True,
            *,
            cancel_futures: bool = False,
        ) -> None:
            if executor is owned_executor:
                calls.append((wait, cancel_futures))
            original_shutdown(
                executor,
                wait=wait,
                cancel_futures=cancel_futures,
            )

        monkeypatch.setattr(
            concurrent.futures.ThreadPoolExecutor,
            "shutdown",
            recording_shutdown,
        )
        await adapter.close()

        assert calls == [(True, True)]

    _run(scenario())


def test_concurrent_owned_executor_closes_share_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        adapter: AsyncExecutor = AsyncExecutor()
        owned_executor: object = vars(adapter)["_executor"]
        shutdown_started: threading.Event = threading.Event()
        release_shutdown: threading.Event = threading.Event()
        calls: list[tuple[bool, bool]] = []
        original_shutdown: Callable[..., None] = (
            concurrent.futures.ThreadPoolExecutor.shutdown
        )

        def gated_shutdown(
            executor: concurrent.futures.ThreadPoolExecutor,
            wait: bool = True,
            *,
            cancel_futures: bool = False,
        ) -> None:
            if executor is owned_executor:
                calls.append((wait, cancel_futures))
                shutdown_started.set()
                if not release_shutdown.wait(timeout=2):
                    raise TimeoutError("test did not release executor shutdown")
            original_shutdown(
                executor,
                wait=wait,
                cancel_futures=cancel_futures,
            )

        monkeypatch.setattr(
            concurrent.futures.ThreadPoolExecutor,
            "shutdown",
            gated_shutdown,
        )
        first_waiter: asyncio.Task[None] = asyncio.create_task(adapter.close())
        second_entered: asyncio.Event = asyncio.Event()

        async def close_again() -> None:
            second_entered.set()
            await adapter.close()

        second_waiter: asyncio.Task[None] = asyncio.create_task(close_again())
        try:
            assert await asyncio.wait_for(
                asyncio.to_thread(shutdown_started.wait, 2),
                timeout=3,
            )
            await asyncio.wait_for(second_entered.wait(), timeout=3)

            assert adapter.closed
            assert not first_waiter.done()
            assert not second_waiter.done()
            shutdown_task: object = vars(adapter).get("_close_task")
            assert isinstance(shutdown_task, asyncio.Task)

            release_shutdown.set()
            await asyncio.wait_for(
                asyncio.gather(first_waiter, second_waiter),
                timeout=3,
            )
            assert calls == [(True, True)]

            await adapter.close()
            assert vars(adapter)["_close_task"] is shutdown_task
        finally:
            release_shutdown.set()
            await asyncio.wait_for(
                asyncio.gather(
                    first_waiter,
                    second_waiter,
                    return_exceptions=True,
                ),
                timeout=3,
            )

    _run(scenario())


def test_concurrent_shutdown_failure_is_shared_and_later_close_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        adapter: AsyncExecutor = AsyncExecutor()
        owned_executor: concurrent.futures.ThreadPoolExecutor = vars(adapter)[
            "_executor"
        ]
        shutdown_started: threading.Event = threading.Event()
        release_failure: threading.Event = threading.Event()
        second_entered: asyncio.Event = asyncio.Event()
        failure: OSError = OSError("cannot shut down executor")
        calls: list[tuple[bool, bool]] = []
        original_shutdown: Callable[..., None] = (
            concurrent.futures.ThreadPoolExecutor.shutdown
        )

        def failing_once_shutdown(
            executor: concurrent.futures.ThreadPoolExecutor,
            wait: bool = True,
            *,
            cancel_futures: bool = False,
        ) -> None:
            if executor is owned_executor:
                calls.append((wait, cancel_futures))
                if len(calls) == 1:
                    shutdown_started.set()
                    if not release_failure.wait(timeout=2):
                        raise TimeoutError("test did not release failed shutdown")
                    raise failure
            original_shutdown(
                executor,
                wait=wait,
                cancel_futures=cancel_futures,
            )

        async def close_second() -> None:
            second_entered.set()
            await adapter.close()

        monkeypatch.setattr(
            concurrent.futures.ThreadPoolExecutor,
            "shutdown",
            failing_once_shutdown,
        )
        first_waiter: asyncio.Task[None] = asyncio.create_task(adapter.close())
        second_waiter: asyncio.Task[None] = asyncio.create_task(close_second())

        try:
            assert await asyncio.wait_for(
                asyncio.to_thread(shutdown_started.wait, 2),
                timeout=3,
            )
            await asyncio.wait_for(second_entered.wait(), timeout=3)
            shared_task: object = vars(adapter).get("_close_task")
            assert isinstance(shared_task, asyncio.Task)
            assert not first_waiter.done()
            assert not second_waiter.done()

            release_failure.set()
            with pytest.raises(OSError) as first_caught:
                await asyncio.wait_for(first_waiter, timeout=3)
            with pytest.raises(OSError) as second_caught:
                await asyncio.wait_for(second_waiter, timeout=3)

            assert first_caught.value is failure
            assert second_caught.value is failure
            assert calls == [(True, True)]
            assert vars(adapter)["_close_task"] is None

            await asyncio.wait_for(adapter.close(), timeout=3)
            retry_task: object = vars(adapter).get("_close_task")
            assert isinstance(retry_task, asyncio.Task)
            assert retry_task is not shared_task
            assert calls == [(True, True), (True, True)]

            await adapter.close()
            assert vars(adapter)["_close_task"] is retry_task
            assert calls == [(True, True), (True, True)]
        finally:
            release_failure.set()
            await asyncio.wait_for(
                asyncio.gather(
                    first_waiter,
                    second_waiter,
                    return_exceptions=True,
                ),
                timeout=3,
            )
            await asyncio.to_thread(
                original_shutdown,
                owned_executor,
                wait=True,
                cancel_futures=True,
            )

    _run(scenario())


def test_cancelled_close_waiter_does_not_cancel_owned_shutdown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        adapter: AsyncExecutor = AsyncExecutor()
        owned_executor: object = vars(adapter)["_executor"]
        shutdown_started: threading.Event = threading.Event()
        release_shutdown: threading.Event = threading.Event()
        calls: list[tuple[bool, bool]] = []
        original_shutdown: Callable[..., None] = (
            concurrent.futures.ThreadPoolExecutor.shutdown
        )

        def gated_shutdown(
            executor: concurrent.futures.ThreadPoolExecutor,
            wait: bool = True,
            *,
            cancel_futures: bool = False,
        ) -> None:
            if executor is owned_executor:
                calls.append((wait, cancel_futures))
                shutdown_started.set()
                if not release_shutdown.wait(timeout=2):
                    raise TimeoutError("test did not release executor shutdown")
            original_shutdown(
                executor,
                wait=wait,
                cancel_futures=cancel_futures,
            )

        monkeypatch.setattr(
            concurrent.futures.ThreadPoolExecutor,
            "shutdown",
            gated_shutdown,
        )
        cancelled_waiter: asyncio.Task[None] = asyncio.create_task(adapter.close())
        current_entered: asyncio.Event = asyncio.Event()

        async def close_currently() -> None:
            current_entered.set()
            await adapter.close()

        current_waiter: asyncio.Task[None] = asyncio.create_task(close_currently())
        try:
            assert await asyncio.wait_for(
                asyncio.to_thread(shutdown_started.wait, 2),
                timeout=3,
            )
            await asyncio.wait_for(current_entered.wait(), timeout=3)
            shutdown_task: object = vars(adapter).get("_close_task")
            assert isinstance(shutdown_task, asyncio.Task)
            assert not current_waiter.done()

            cancelled_waiter.cancel()
            with pytest.raises(asyncio.CancelledError):
                await cancelled_waiter
            assert not shutdown_task.cancelled()
            assert not shutdown_task.done()
            assert not current_waiter.done()

            release_shutdown.set()
            await asyncio.wait_for(current_waiter, timeout=3)
            await adapter.close()

            assert vars(adapter)["_close_task"] is shutdown_task
            assert calls == [(True, True)]
        finally:
            release_shutdown.set()
            await asyncio.wait_for(
                asyncio.gather(
                    current_waiter,
                    cancelled_waiter,
                    return_exceptions=True,
                ),
                timeout=3,
            )

    _run(scenario())


def test_socketpair_round_trip_uses_no_external_network_service() -> None:
    async def scenario() -> None:
        adapter: AsyncExecutor = AsyncExecutor()
        reader: socket.socket
        writer: socket.socket
        reader, writer = socket.socketpair()
        try:
            receive_task: asyncio.Task[bytes] = asyncio.create_task(
                adapter.run(reader.recv, 4)
            )
            writer.sendall(b"ping")
            assert await asyncio.wait_for(receive_task, timeout=3) == b"ping"
        finally:
            reader.close()
            writer.close()
            await adapter.close()

    _run(scenario())


def test_async_file_round_trip_and_rename(tmp_path: Path) -> None:
    async def scenario() -> None:
        source: Path = tmp_path / "source.txt"
        target: Path = tmp_path / "renamed.bin"
        async_file: AsyncioFile = AsyncioFile(source)

        entered: AsyncioFile
        async with async_file as entered:
            assert entered is async_file
            assert entered.path == source
            assert not await entered.exists()
            assert await entered.write_text("héllo\n") == len("héllo\n")
            assert await entered.read_text() == "héllo\n"
            assert await entered.write_bytes(b"\x00\x01\x02") == 3
            assert await entered.read_bytes() == b"\x00\x01\x02"
            assert await entered.rename(target) == target

        assert async_file.closed
        assert target.read_bytes() == b"\x00\x01\x02"
        with pytest.raises(RuntimeError, match="closed"):
            await async_file.exists()

    _run(scenario())


def test_text_methods_have_keyword_only_utf8_strict_contract() -> None:
    read_parameters: dict[str, inspect.Parameter] = dict(
        inspect.signature(AsyncioFile.read_text).parameters
    )
    write_parameters: dict[str, inspect.Parameter] = dict(
        inspect.signature(AsyncioFile.write_text).parameters
    )

    assert read_parameters["encoding"].kind is inspect.Parameter.KEYWORD_ONLY
    assert read_parameters["encoding"].default == "utf-8"
    assert read_parameters["errors"].kind is inspect.Parameter.KEYWORD_ONLY
    assert read_parameters["errors"].default == "strict"
    assert write_parameters["encoding"].kind is inspect.Parameter.KEYWORD_ONLY
    assert write_parameters["encoding"].default == "utf-8"
    assert write_parameters["errors"].kind is inspect.Parameter.KEYWORD_ONLY
    assert write_parameters["errors"].default == "strict"
    assert "newline" not in write_parameters


def test_async_file_with_injected_runner_does_not_close_runner(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        runner: AsyncExecutor = AsyncExecutor()
        async_file: AsyncioFile = AsyncioFile(
            tmp_path / "owned-by-caller.txt",
            runner,
        )
        try:
            async with async_file:
                await async_file.write_text("contents")

            assert not runner.closed
            assert await runner.run(_multiply, 5, 5) == 25
            assert await async_file.read_text() == "contents"
        finally:
            await runner.close()

    _run(scenario())


def test_owned_async_file_close_inherits_shared_shielded_shutdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def scenario() -> None:
        async_file: AsyncioFile = AsyncioFile(tmp_path / "owned-runner.txt")
        runner: AsyncExecutor = vars(async_file)["_runner"]
        owned_executor: object = vars(runner)["_executor"]
        shutdown_started: threading.Event = threading.Event()
        release_shutdown: threading.Event = threading.Event()
        calls: list[tuple[bool, bool]] = []
        original_shutdown: Callable[..., None] = (
            concurrent.futures.ThreadPoolExecutor.shutdown
        )

        def gated_shutdown(
            executor: concurrent.futures.ThreadPoolExecutor,
            wait: bool = True,
            *,
            cancel_futures: bool = False,
        ) -> None:
            if executor is owned_executor:
                calls.append((wait, cancel_futures))
                shutdown_started.set()
                if not release_shutdown.wait(timeout=2):
                    raise TimeoutError("test did not release file runner shutdown")
            original_shutdown(
                executor,
                wait=wait,
                cancel_futures=cancel_futures,
            )

        monkeypatch.setattr(
            concurrent.futures.ThreadPoolExecutor,
            "shutdown",
            gated_shutdown,
        )
        cancelled_waiter: asyncio.Task[None] = asyncio.create_task(async_file.close())
        current_entered: asyncio.Event = asyncio.Event()

        async def close_currently() -> None:
            current_entered.set()
            await async_file.close()

        current_waiter: asyncio.Task[None] = asyncio.create_task(close_currently())
        try:
            assert await asyncio.wait_for(
                asyncio.to_thread(shutdown_started.wait, 2),
                timeout=3,
            )
            await asyncio.wait_for(current_entered.wait(), timeout=3)
            shutdown_task: object = vars(runner).get("_close_task")
            assert isinstance(shutdown_task, asyncio.Task)
            assert not current_waiter.done()

            cancelled_waiter.cancel()
            with pytest.raises(asyncio.CancelledError):
                await cancelled_waiter
            assert not shutdown_task.cancelled()
            assert not shutdown_task.done()
            assert not current_waiter.done()

            release_shutdown.set()
            await asyncio.wait_for(current_waiter, timeout=3)
            await async_file.close()

            assert vars(runner)["_close_task"] is shutdown_task
            assert calls == [(True, True)]
        finally:
            release_shutdown.set()
            await asyncio.wait_for(
                asyncio.gather(
                    current_waiter,
                    cancelled_waiter,
                    return_exceptions=True,
                ),
                timeout=3,
            )

    _run(scenario())


def test_import_is_silent_and_does_not_create_threads() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_13_async_io.exercise_02.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_guarded_demo_runs() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "CH_13_async_io.exercise_02.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert completed.returncode == 0
    assert completed.stdout == (
        '"""Run synchronous process, file, and network operations in executors."""\n'
    )
    assert completed.stderr == ""
