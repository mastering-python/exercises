"""Manage explicitly registered asynchronous resources."""

from __future__ import annotations

import abc
import asyncio
from types import TracebackType
from typing import ClassVar


class CloseFailures(RuntimeError):
    """Report every ordinary exception raised during one close pass."""

    def __init__(self, failures: tuple[Exception, ...]) -> None:
        self.failures: tuple[Exception, ...] = failures
        super().__init__(f"{len(failures)} resource(s) failed to close")


class AsyncBase(abc.ABC):
    """Base class for resources with deterministic asynchronous cleanup."""

    _instances: ClassVar[list[AsyncBase]] = []

    def __init__(self) -> None:
        self._closed: bool = False
        self._close_task: asyncio.Task[None] | None = None
        AsyncBase._instances.append(self)

    @property
    def closed(self) -> bool:
        """Return whether cleanup completed successfully."""
        return self._closed

    @abc.abstractmethod
    async def _close(self) -> None:
        """Release this resource's asynchronous state."""

    async def close(self) -> None:
        """Close once, retaining failed resources for a later retry."""
        if self._closed:
            return

        close_task: asyncio.Task[None] | None = self._close_task
        if close_task is None:
            close_task = asyncio.create_task(self._close_once())
            self._close_task = close_task
        try:
            await close_task
        finally:
            if close_task.done() and self._close_task is close_task:
                self._close_task = None

    async def _close_once(self) -> None:
        await self._close()
        self._closed = True
        AsyncBase._unregister(self)

    @classmethod
    def pending_count(cls: type[AsyncBase]) -> int:
        """Return the number of registered resources awaiting cleanup."""
        return len(AsyncBase._instances)

    @classmethod
    async def close_all(cls: type[AsyncBase]) -> None:
        """Attempt a LIFO close pass and aggregate ordinary exceptions."""
        failures: list[Exception] = []
        resources: tuple[AsyncBase, ...] = tuple(AsyncBase._instances)

        for resource in reversed(resources):
            try:
                await resource.close()
            except Exception as error:
                failures.append(error)

        if failures:
            raise CloseFailures(tuple(failures))

    @staticmethod
    def _unregister(resource: AsyncBase) -> None:
        for index, registered in enumerate(AsyncBase._instances):
            if registered is resource:
                del AsyncBase._instances[index]
                return


class AsyncManager:
    """Close all registered resources when leaving an async context."""

    async def __aenter__(self) -> AsyncManager:
        return self

    async def __aexit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        del exception_type, exception, traceback
        await AsyncBase.close_all()
        return False


class DemoResource(AsyncBase):
    def __init__(self, name: str) -> None:
        self._name: str = name
        super().__init__()

    async def _close(self) -> None:
        print(f"closed {self._name}")


async def main() -> None:
    """Demonstrate automatic LIFO cleanup."""
    async with AsyncManager():
        DemoResource("demo")


if __name__ == "__main__":
    asyncio.run(main())
