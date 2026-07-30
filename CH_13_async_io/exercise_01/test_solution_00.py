"""Tests explicit asynchronous resource lifecycle management."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from collections.abc import Coroutine
from pathlib import Path
from types import TracebackType
from typing import Any, TypeVar, cast

import pytest

from CH_13_async_io.exercise_01.solution_00 import (
    AsyncBase,
    AsyncManager,
    CloseFailures,
)

_T = TypeVar("_T")


def _run(coroutine: Coroutine[Any, Any, _T]) -> _T:
    return asyncio.run(coroutine)


class _Resource(AsyncBase):
    def __init__(
        self,
        name: str,
        events: list[str],
        failures: list[BaseException] | None = None,
    ) -> None:
        self.name: str = name
        self.events: list[str] = events
        self.failures: list[BaseException] = failures or []
        self.attempts: int = 0
        super().__init__()

    async def _close(self) -> None:
        self.attempts += 1
        self.events.append(self.name)
        if self.failures:
            raise self.failures.pop(0)


class _CoalescingResource(AsyncBase):
    def __init__(
        self,
        *,
        failure: BaseException | None = None,
    ) -> None:
        self.entered: asyncio.Event = asyncio.Event()
        self.release: asyncio.Event = asyncio.Event()
        self.failure: BaseException | None = failure
        self.attempts: int = 0
        super().__init__()

    async def _close(self) -> None:
        self.attempts += 1
        self.entered.set()
        await self.release.wait()
        if self.failure is not None:
            raise self.failure


class _BodyFailure(RuntimeError):
    pass


class _CleanupFailure(RuntimeError):
    pass


class _ControlFlow(BaseException):
    pass


def test_close_all_uses_lifo_order_and_clears_successful_resources() -> None:
    async def scenario() -> None:
        events: list[str] = []
        first: _Resource = _Resource("first", events)
        second: _Resource = _Resource("second", events)

        assert AsyncBase.pending_count() == 2
        await AsyncBase.close_all()

        assert events == ["second", "first"]
        assert first.closed
        assert second.closed
        assert AsyncBase.pending_count() == 0

    _run(scenario())


def test_resource_close_is_idempotent() -> None:
    async def scenario() -> None:
        events: list[str] = []
        resource: _Resource = _Resource("resource", events)

        await resource.close()
        await resource.close()
        await AsyncBase.close_all()

        assert resource.attempts == 1
        assert events == ["resource"]
        assert AsyncBase.pending_count() == 0

    _run(scenario())


def test_concurrent_close_calls_share_one_successful_attempt() -> None:
    async def scenario() -> None:
        resource: _CoalescingResource = _CoalescingResource()
        second_started: asyncio.Event = asyncio.Event()

        async def close_second() -> None:
            second_started.set()
            await resource.close()

        first: asyncio.Task[None] = asyncio.create_task(resource.close())
        await asyncio.wait_for(resource.entered.wait(), timeout=2)
        second: asyncio.Task[None] = asyncio.create_task(close_second())
        await asyncio.wait_for(second_started.wait(), timeout=2)

        assert resource.attempts == 1
        assert not first.done()
        assert not second.done()
        resource.release.set()
        await asyncio.wait_for(asyncio.gather(first, second), timeout=2)
        assert resource.closed
        assert AsyncBase.pending_count() == 0

    _run(scenario())


def test_concurrent_close_failure_is_shared_and_resource_is_retryable() -> None:
    async def scenario() -> None:
        failure: RuntimeError = RuntimeError("close failed")
        resource: _CoalescingResource = _CoalescingResource(failure=failure)
        second_started: asyncio.Event = asyncio.Event()

        async def close_second() -> None:
            second_started.set()
            await resource.close()

        first: asyncio.Task[None] = asyncio.create_task(resource.close())
        await asyncio.wait_for(resource.entered.wait(), timeout=2)
        second: asyncio.Task[None] = asyncio.create_task(close_second())
        await asyncio.wait_for(second_started.wait(), timeout=2)
        resource.release.set()

        results: tuple[BaseException | None, BaseException | None] = cast(
            tuple[BaseException | None, BaseException | None],
            tuple(
                await asyncio.wait_for(
                    asyncio.gather(
                        first,
                        second,
                        return_exceptions=True,
                    ),
                    timeout=2,
                )
            ),
        )
        assert results == (failure, failure)
        assert resource.attempts == 1
        assert not resource.closed
        assert AsyncBase.pending_count() == 1

        resource.failure = None
        await resource.close()
        assert resource.attempts == 2
        assert resource.closed
        assert AsyncBase.pending_count() == 0

    _run(scenario())


def test_concurrent_close_cancellation_is_shared_and_resource_is_retryable() -> None:
    async def scenario() -> None:
        resource: _CoalescingResource = _CoalescingResource()
        second_started: asyncio.Event = asyncio.Event()

        async def close_second() -> None:
            second_started.set()
            await resource.close()

        first: asyncio.Task[None] = asyncio.create_task(resource.close())
        await asyncio.wait_for(resource.entered.wait(), timeout=2)
        second: asyncio.Task[None] = asyncio.create_task(close_second())
        await asyncio.wait_for(second_started.wait(), timeout=2)

        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(second, timeout=2)

        assert resource.attempts == 1
        assert not resource.closed
        assert AsyncBase.pending_count() == 1

        resource.release.set()
        await resource.close()
        assert resource.attempts == 2
        assert resource.closed
        assert AsyncBase.pending_count() == 0

    _run(scenario())


def test_close_all_aggregates_exceptions_and_retries_failed_resources() -> None:
    async def scenario() -> None:
        events: list[str] = []
        first_error: ValueError = ValueError("first failed")
        last_error: LookupError = LookupError("last failed")
        first: _Resource = _Resource("first", events, [first_error])
        middle: _Resource = _Resource("middle", events)
        last: _Resource = _Resource("last", events, [last_error])

        with pytest.raises(CloseFailures) as caught:
            await AsyncBase.close_all()

        assert caught.value.failures == (last_error, first_error)
        assert events == ["last", "middle", "first"]
        assert AsyncBase.pending_count() == 2
        assert not first.closed
        assert middle.closed
        assert not last.closed

        await AsyncBase.close_all()

        assert events == ["last", "middle", "first", "last", "first"]
        assert first.closed
        assert last.closed
        assert AsyncBase.pending_count() == 0

    _run(scenario())


def test_base_exception_propagates_without_being_aggregated() -> None:
    async def scenario() -> None:
        events: list[str] = []
        earlier: _Resource = _Resource("earlier", events)
        control: _ControlFlow = _ControlFlow()
        interrupted: _Resource = _Resource(
            "interrupted",
            events,
            [control],
        )
        later: _Resource = _Resource("later", events)

        with pytest.raises(_ControlFlow) as caught:
            await AsyncBase.close_all()

        assert caught.value is control
        assert events == ["later", "interrupted"]
        assert later.closed
        assert not interrupted.closed
        assert not earlier.closed
        assert AsyncBase.pending_count() == 2
        await AsyncBase.close_all()

    _run(scenario())


def test_cancelled_error_propagates_and_resource_remains_retryable() -> None:
    async def scenario() -> None:
        events: list[str] = []
        resource: _Resource = _Resource(
            "cancelled",
            events,
            [asyncio.CancelledError()],
        )

        with pytest.raises(asyncio.CancelledError):
            await AsyncBase.close_all()

        assert AsyncBase.pending_count() == 1
        assert not resource.closed
        await AsyncBase.close_all()
        assert resource.closed
        assert AsyncBase.pending_count() == 0

    _run(scenario())


def test_context_closes_resources_and_preserves_body_exception() -> None:
    async def scenario() -> None:
        manager: AsyncManager = AsyncManager()
        events: list[str] = []
        resource: _Resource | None = None

        with pytest.raises(_BodyFailure, match="body failed"):
            async with manager as entered:
                assert entered is manager
                resource = _Resource("resource", events)
                raise _BodyFailure("body failed")

        assert events == ["resource"]
        assert resource is not None
        assert resource.closed
        assert AsyncBase.pending_count() == 0

    _run(scenario())


def test_cleanup_failure_propagates_when_body_also_fails() -> None:
    async def scenario() -> None:
        manager: AsyncManager = AsyncManager()
        cleanup_error: _CleanupFailure = _CleanupFailure("cleanup failed")

        with pytest.raises(CloseFailures) as caught:
            async with manager:
                _Resource("resource", [], [cleanup_error])
                raise _BodyFailure("body failed")

        assert caught.value.failures == (cleanup_error,)
        assert isinstance(caught.value.__context__, _BodyFailure)
        assert AsyncBase.pending_count() == 1
        await AsyncBase.close_all()

    _run(scenario())


def test_cleanup_failure_propagates_when_context_body_succeeds() -> None:
    async def scenario() -> None:
        manager: AsyncManager = AsyncManager()
        cleanup_error: _CleanupFailure = _CleanupFailure("cleanup failed")

        with pytest.raises(CloseFailures) as caught:
            async with manager:
                _Resource("resource", [], [cleanup_error])

        assert caught.value.failures == (cleanup_error,)
        assert AsyncBase.pending_count() == 1
        await AsyncBase.close_all()

    _run(scenario())


def test_all_subclasses_use_one_base_registry_without_shadow_state() -> None:
    class OtherResource(_Resource):
        pass

    async def scenario() -> None:
        events: list[str] = []
        first: _Resource = _Resource("first", events)
        second: OtherResource = OtherResource("second", events)

        assert _Resource.pending_count() == 2
        assert OtherResource.pending_count() == 2
        await OtherResource.close_all()

        assert events == ["second", "first"]
        assert first.closed
        assert second.closed
        assert AsyncBase.pending_count() == 0

    _run(scenario())


def test_close_failures_is_a_runtime_error() -> None:
    assert issubclass(CloseFailures, RuntimeError)


def test_async_base_cannot_be_instantiated_without_close_hook() -> None:
    class IncompleteResource(AsyncBase):
        pass

    with pytest.raises(TypeError):
        IncompleteResource()  # type: ignore[abstract]


def test_context_exit_annotation_accepts_standard_protocol_shape() -> None:
    async def call_exit(
        manager: AsyncManager,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        return await manager.__aexit__(
            exception_type,
            exception,
            traceback,
        )

    assert _run(call_exit(AsyncManager(), None, None, None)) is False


def test_import_is_silent_and_does_not_start_async_work() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_13_async_io.exercise_01.solution_00",
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
            "CH_13_async_io.exercise_01.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert completed.returncode == 0
    assert completed.stdout == "closed demo\n"
    assert completed.stderr == ""
