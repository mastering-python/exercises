"""Warn when call duration differs substantially from prior runs."""

import time
import warnings
from collections.abc import Callable
from dataclasses import dataclass
from functools import update_wrapper
from types import MethodType
from typing import Generic, ParamSpec, Protocol, TypeVar, cast, overload

Parameters = ParamSpec("Parameters")
Result = TypeVar("Result")
BoundResult = TypeVar("BoundResult", covariant=True)


@dataclass(frozen=True)
class RuntimeStats:
    """Successful-call runtime statistics."""

    calls: int
    total_seconds: float

    @property
    def average_seconds(self) -> float:
        """Return mean duration, or zero before the first successful call."""
        return self.total_seconds / self.calls if self.calls else 0.0


class _BoundRuntimeMonitor(Protocol[BoundResult]):
    """Callable bound monitor exposing its shared statistics."""

    @property
    def stats(self) -> RuntimeStats:
        """Return statistics owned by the class-level monitor."""
        ...

    def __call__(self, *args: object, **kwargs: object) -> BoundResult:
        """Invoke the monitor with its bound instance."""
        ...


class RuntimeMonitor(Generic[Parameters, Result]):
    """Callable wrapper comparing each duration with the prior average."""

    __name__: str
    __wrapped__: Callable[Parameters, Result]

    def __init__(
        self,
        function: Callable[Parameters, Result],
        clock: Callable[[], float] = time.perf_counter,
        max_deviation: float = 0.25,
    ) -> None:
        if not max_deviation >= 0:
            raise ValueError("max_deviation must not be negative")
        self._function: Callable[Parameters, Result] = function
        self._clock: Callable[[], float] = clock
        self._max_deviation: float = max_deviation
        self.stats: RuntimeStats = RuntimeStats(0, 0.0)
        update_wrapper(self, function, updated=())

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object] | None = None,
    ) -> "RuntimeMonitor[Parameters, Result]": ...

    @overload
    def __get__(
        self,
        instance: object,
        owner: type[object] | None = None,
    ) -> _BoundRuntimeMonitor[Result]: ...

    def __get__(
        self,
        instance: object | None,
        owner: type[object] | None = None,
    ) -> "RuntimeMonitor[Parameters, Result] | _BoundRuntimeMonitor[Result]":
        """Bind the shared monitor when accessed through an instance."""
        if instance is None:
            return self
        return cast(_BoundRuntimeMonitor[Result], MethodType(self, instance))

    def __call__(
        self,
        *args: Parameters.args,
        **kwargs: Parameters.kwargs,
    ) -> Result:
        """Run the callable, update statistics, and warn on deviation."""
        started: float = self._clock()
        value: Result = self._function(*args, **kwargs)
        finished: float = self._clock()
        duration: float = finished - started
        if duration < 0:
            raise ValueError("clock moved backwards")

        previous_stats: RuntimeStats = self.stats
        previous_average: float = previous_stats.average_seconds
        self.stats = RuntimeStats(
            previous_stats.calls + 1,
            previous_stats.total_seconds + duration,
        )
        if (
            previous_stats.calls > 0
            and previous_average > 0
            and abs(duration - previous_average)
            > previous_average * self._max_deviation
        ):
            warnings.warn(
                "runtime deviated from the previous average",
                RuntimeWarning,
                stacklevel=2,
            )
        return value


def monitor_runtime(
    *,
    clock: Callable[[], float] = time.perf_counter,
    max_deviation: float = 0.25,
) -> Callable[
    [Callable[Parameters, Result]],
    RuntimeMonitor[Parameters, Result],
]:
    """Create a runtime monitor decorator."""
    if not max_deviation >= 0:
        raise ValueError("max_deviation must not be negative")

    def decorate(
        function: Callable[Parameters, Result],
    ) -> RuntimeMonitor[Parameters, Result]:
        return RuntimeMonitor(function, clock, max_deviation)

    return decorate


def main() -> None:
    """Demonstrate deterministic runtime statistics."""
    samples: list[float] = [0.0, 1.0, 2.0, 3.0]

    @monitor_runtime(clock=lambda: samples.pop(0))
    def operation() -> str:
        return "finished"

    print(operation())
    print(operation())
    print(operation.stats)


if __name__ == "__main__":
    main()
