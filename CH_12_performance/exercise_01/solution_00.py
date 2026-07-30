"""Warn when a successful call's sampled memory grows."""

import tracemalloc
import warnings
from collections.abc import Callable
from functools import update_wrapper
from types import MethodType
from typing import Generic, ParamSpec, TypeVar, overload

Parameters = ParamSpec("Parameters")
Result = TypeVar("Result")


def _traced_bytes() -> int:
    """Return currently traced bytes, starting tracemalloc when necessary."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    current: int
    current, _ = tracemalloc.get_traced_memory()
    return current


class MemoryGrowthMonitor(Generic[Parameters, Result]):
    """Callable wrapper retaining the previous successful sample."""

    __name__: str
    __wrapped__: Callable[Parameters, Result]

    def __init__(
        self,
        function: Callable[Parameters, Result],
        sampler: Callable[[], int] = _traced_bytes,
        tolerance_bytes: int = 0,
    ) -> None:
        if tolerance_bytes < 0:
            raise ValueError("tolerance_bytes must not be negative")
        self._function: Callable[Parameters, Result] = function
        self._sampler: Callable[[], int] = sampler
        self._tolerance_bytes: int = tolerance_bytes
        self._previous: int | None = None
        update_wrapper(self, function, updated=())

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object] | None = None,
    ) -> "MemoryGrowthMonitor[Parameters, Result]": ...

    @overload
    def __get__(
        self,
        instance: object,
        owner: type[object] | None = None,
    ) -> Callable[..., Result]: ...

    def __get__(
        self,
        instance: object | None,
        owner: type[object] | None = None,
    ) -> "MemoryGrowthMonitor[Parameters, Result] | Callable[..., Result]":
        """Bind the shared monitor when accessed through an instance."""
        if instance is None:
            return self
        return MethodType(self, instance)

    def __call__(
        self,
        *args: Parameters.args,
        **kwargs: Parameters.kwargs,
    ) -> Result:
        """Run the callable, sample memory, and warn about excess growth."""
        value: Result = self._function(*args, **kwargs)
        current: int = self._sampler()
        previous: int | None = self._previous
        self._previous = current
        if previous is not None:
            growth: int = current - previous
            if growth > self._tolerance_bytes:
                warnings.warn(
                    f"sampled memory grew by {growth} bytes",
                    ResourceWarning,
                    stacklevel=2,
                )
        return value


def monitor_memory_growth(
    *,
    sampler: Callable[[], int] = _traced_bytes,
    tolerance_bytes: int = 0,
) -> Callable[
    [Callable[Parameters, Result]],
    MemoryGrowthMonitor[Parameters, Result],
]:
    """Create a monitor decorator with an injectable sampler."""
    if tolerance_bytes < 0:
        raise ValueError("tolerance_bytes must not be negative")

    def decorate(
        function: Callable[Parameters, Result],
    ) -> MemoryGrowthMonitor[Parameters, Result]:
        return MemoryGrowthMonitor(function, sampler, tolerance_bytes)

    return decorate


def main() -> None:
    """Demonstrate deterministic sampled growth."""
    samples: list[int] = [100, 120]

    @monitor_memory_growth(sampler=lambda: samples.pop(0))
    def operation() -> str:
        return "finished"

    print(operation())
    print(operation())


if __name__ == "__main__":
    main()
