"""Run synchronous process, file, and network operations in executors."""

from __future__ import annotations

import asyncio
import concurrent.futures
import functools
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")
_T = TypeVar("_T")


class AsyncExecutor:
    """Adapt a synchronous executor to an awaitable interface."""

    def __init__(
        self,
        executor: concurrent.futures.Executor | None = None,
    ) -> None:
        if executor is None:
            self._executor: concurrent.futures.Executor = (
                concurrent.futures.ThreadPoolExecutor()
            )
            self._owns_executor: bool = True
        else:
            self._executor = executor
            self._owns_executor = False
        self._closed: bool = False
        self._close_task: asyncio.Task[None] | None = None

    @property
    def closed(self) -> bool:
        """Return whether this adapter rejects new work."""
        return self._closed

    async def run(
        self,
        function: Callable[_P, _T],
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> _T:
        """Run *function* in the configured executor."""
        if self._closed:
            raise RuntimeError("executor is closed")

        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        call: functools.partial[_T] = functools.partial(
            function,
            *args,
            **kwargs,
        )
        return await loop.run_in_executor(self._executor, call)

    async def close(self) -> None:
        """Reject new work and asynchronously stop an owned thread pool."""
        close_task: asyncio.Task[None] | None = self._close_task
        if close_task is None:
            self._closed = True
            close_task = asyncio.create_task(self._close_executor())
            self._close_task = close_task

        try:
            await asyncio.shield(close_task)
        except BaseException:
            if (
                self._close_task is close_task
                and close_task.done()
                and (close_task.cancelled() or close_task.exception() is not None)
            ):
                self._close_task = None
            raise

    async def _close_executor(self) -> None:
        if self._owns_executor:
            await asyncio.to_thread(
                self._executor.shutdown,
                wait=True,
                cancel_futures=True,
            )

    async def __aenter__(self) -> AsyncExecutor:
        if self._closed:
            raise RuntimeError("executor is closed")
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        del exception_type, exception, traceback
        await self.close()
        return False


class AsyncioFile:
    """Expose common :class:`pathlib.Path` operations asynchronously."""

    def __init__(
        self,
        path: Path,
        runner: AsyncExecutor | None = None,
    ) -> None:
        self.path: Path = path
        self._runner: AsyncExecutor = runner if runner is not None else AsyncExecutor()
        self._owns_runner: bool = runner is None

    @property
    def closed(self) -> bool:
        """Return whether the internal executor adapter is closed."""
        return self._runner.closed

    async def exists(self) -> bool:
        return await self._runner.run(self.path.exists)

    async def read_text(
        self,
        *,
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> str:
        return await self._runner.run(
            self.path.read_text,
            encoding=encoding,
            errors=errors,
        )

    async def write_text(
        self,
        data: str,
        *,
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> int:
        return await self._runner.run(
            self.path.write_text,
            data,
            encoding=encoding,
            errors=errors,
        )

    async def read_bytes(self) -> bytes:
        return await self._runner.run(self.path.read_bytes)

    async def write_bytes(self, data: bytes) -> int:
        return await self._runner.run(self.path.write_bytes, data)

    async def rename(self, target: Path) -> Path:
        return await self._runner.run(self.path.rename, target)

    async def close(self) -> None:
        if self._owns_runner:
            await self._runner.close()

    async def __aenter__(self) -> AsyncioFile:
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        del exception_type, exception, traceback
        await self.close()
        return False


async def main() -> None:
    """Read this source file through an executor."""
    async_file: AsyncioFile = AsyncioFile(Path(__file__))
    async with async_file:
        print((await async_file.read_text()).splitlines()[0])


if __name__ == "__main__":
    asyncio.run(main())
