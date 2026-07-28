"""Track function execution time with an injectable clock and reporter."""

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from time import perf_counter
from typing import ParamSpec, TypeVar, overload

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(frozen=True)
class Timing:
    """The outcome and duration of one tracked function call."""

    label: str
    elapsed: float
    failed: bool


def print_timing(timing: Timing) -> None:
    """Print a timing report."""
    status: str = "failed" if timing.failed else "completed"
    print(f"{timing.label} {status} in {timing.elapsed:.6f}s")


@overload
def track(function: Callable[P, R], /) -> Callable[P, R]: ...


@overload
def track(
    *,
    label: str | None = None,
    clock: Callable[[], float] = perf_counter,
    reporter: Callable[[Timing], None] = print_timing,
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def track(
    function: Callable[P, R] | None = None,
    /,
    *,
    label: str | None = None,
    clock: Callable[[], float] = perf_counter,
    reporter: Callable[[Timing], None] = print_timing,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorate a function and report each call's duration and outcome."""

    def decorate(target: Callable[P, R]) -> Callable[P, R]:
        timing_label: str = target.__name__ if label is None else label

        @wraps(target)
        def tracked(*args: P.args, **kwargs: P.kwargs) -> R:
            started_at: float = clock()
            failed: bool = False
            try:
                return target(*args, **kwargs)
            except BaseException:
                failed = True
                raise
            finally:
                elapsed: float = clock() - started_at
                reporter(Timing(label=timing_label, elapsed=elapsed, failed=failed))

        return tracked

    if function is None:
        return decorate
    return decorate(function)


if __name__ == "__main__":

    @track(label="slow function")
    def slow_function() -> None:
        from time import sleep

        sleep(0.5)

    slow_function()
