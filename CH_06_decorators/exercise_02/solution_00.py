"""Track call timing and aggregate per-decorator statistics."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from functools import wraps
from time import perf_counter
from typing import ParamSpec, Protocol, TypeVar, cast, overload

from CH_06_decorators.exercise_01.solution_00 import (
    Timing,
    print_timing,
    resolve_label,
    select_wrapper_metadata,
)

P = ParamSpec("P")
R = TypeVar("R")
R_co = TypeVar("R_co", covariant=True)


@dataclass
class TimingStats:
    """Mutable aggregate execution-time statistics in seconds."""

    count: int = 0
    total: float = 0.0
    minimum: float | None = None
    maximum: float | None = None

    @property
    def average(self) -> float | None:
        """Return mean elapsed seconds, or ``None`` before the first record."""
        if self.count == 0:
            return None
        return self.total / self.count

    def record(self, elapsed: float) -> None:
        """Add one completed duration to the aggregates."""
        self.count += 1
        self.total += elapsed
        if self.minimum is None or elapsed < self.minimum:
            self.minimum = elapsed
        if self.maximum is None or elapsed > self.maximum:
            self.maximum = elapsed


class TrackedCallable(Protocol[P, R_co]):
    """Callable carrying mutable timing statistics and a printer."""

    stats: TimingStats

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co:
        """Call the wrapped target."""
        ...

    print_stats: Callable[[], None]


def _format_duration(duration: float | None) -> str:
    if duration is None:
        return "n/a"
    return f"{duration:.6f}s"


def _decorate(
    function: Callable[P, R],
    *,
    label: str | None,
    clock: Callable[[], float],
    reporter: Callable[[Timing], None],
) -> TrackedCallable[P, R]:
    timing_label: str = resolve_label(function, label)
    stats: TimingStats = TimingStats()
    wrapper_metadata: tuple[tuple[str, ...], tuple[str, ...]] = select_wrapper_metadata(
        function
    )
    wrapper_assignments: tuple[str, ...] = wrapper_metadata[0]
    wrapper_updates: tuple[str, ...] = wrapper_metadata[1]

    def finish(started_at: float, *, failed: bool) -> None:
        elapsed: float = clock() - started_at
        timing: Timing = Timing(
            label=timing_label,
            elapsed=elapsed,
            failed=failed,
        )
        stats.record(elapsed)
        reporter(timing)

    @wraps(function, assigned=wrapper_assignments, updated=wrapper_updates)
    def tracked(*args: P.args, **kwargs: P.kwargs) -> R:
        started_at: float = clock()
        try:
            result: R = function(*args, **kwargs)
        except BaseException:
            try:
                finish(started_at, failed=True)
            except BaseException:
                pass
            raise

        finish(started_at, failed=False)
        return result

    def print_stats() -> None:
        print(
            f"{timing_label} stats: count={stats.count}, "
            f"total={stats.total:.6f}s, "
            f"minimum={_format_duration(stats.minimum)}, "
            f"maximum={_format_duration(stats.maximum)}, "
            f"average={_format_duration(stats.average)}"
        )

    tracked_callable: TrackedCallable[P, R] = cast(
        TrackedCallable[P, R],
        tracked,
    )
    tracked_callable.stats = stats
    tracked_callable.print_stats = print_stats
    return tracked_callable


@overload
def track(
    function: Callable[P, R],
    /,
    *,
    label: str | None = None,
    clock: Callable[[], float] = perf_counter,
    reporter: Callable[[Timing], None] = print_timing,
) -> TrackedCallable[P, R]: ...


@overload
def track(
    function: None = None,
    /,
    *,
    label: str | None = None,
    clock: Callable[[], float] = perf_counter,
    reporter: Callable[[Timing], None] = print_timing,
) -> Callable[[Callable[P, R]], TrackedCallable[P, R]]: ...


def track(
    function: Callable[P, R] | None = None,
    /,
    *,
    label: str | None = None,
    clock: Callable[[], float] = perf_counter,
    reporter: Callable[[Timing], None] = print_timing,
) -> TrackedCallable[P, R] | Callable[[Callable[P, R]], TrackedCallable[P, R]]:
    """Decorate a function and aggregate every completed call duration."""
    if function is not None:
        return _decorate(
            function,
            label=label,
            clock=clock,
            reporter=reporter,
        )

    def decorate(target: Callable[P, R]) -> TrackedCallable[P, R]:
        return _decorate(
            target,
            label=label,
            clock=clock,
            reporter=reporter,
        )

    return decorate


if __name__ == "__main__":
    readings: Iterator[float] = iter((10.0, 10.25, 20.0, 21.5))

    @track(label="example", clock=readings.__next__)
    def example(value: int) -> int:
        return value * 2

    example(3)
    example(4)
    example.print_stats()
