"""Measure callable duration without coupling tests to wall-clock speed."""

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, ParamSpec, TypeVar

Parameters = ParamSpec("Parameters")
Result = TypeVar("Result")


@dataclass(frozen=True)
class TimedResult(Generic[Result]):
    """A callable's return value and elapsed monotonic seconds."""

    value: Result
    seconds: float


class CallTimer:
    """Measure calls with an injectable monotonic clock."""

    def __init__(
        self,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._clock: Callable[[], float] = clock

    def measure(
        self,
        function: Callable[Parameters, Result],
        *args: Parameters.args,
        **kwargs: Parameters.kwargs,
    ) -> TimedResult[Result]:
        """Run a callable once and return its value and duration."""
        started: float = self._clock()
        value: Result = function(*args, **kwargs)
        finished: float = self._clock()
        seconds: float = finished - started
        if seconds < 0:
            raise ValueError("clock moved backwards")
        return TimedResult(value=value, seconds=seconds)


def measure_call(
    function: Callable[Parameters, Result],
    *args: Parameters.args,
    **kwargs: Parameters.kwargs,
) -> TimedResult[Result]:
    """Measure a callable with ``time.perf_counter``."""
    return CallTimer().measure(function, *args, **kwargs)


def main() -> None:
    """Demonstrate the default monotonic timer."""
    print(measure_call(sum, [1, 2, 3]))


if __name__ == "__main__":
    main()
