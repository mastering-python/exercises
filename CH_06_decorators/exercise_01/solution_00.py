"""Track function execution time with an injectable clock and reporter."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import WRAPPER_ASSIGNMENTS, WRAPPER_UPDATES, wraps
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


def resolve_label(
    function: Callable[..., object],
    label: str | None,
) -> str:
    """Return an explicit label or a deterministic callable-derived default."""
    if label is not None:
        return label

    function_name: object = getattr(function, "__name__", None)
    if isinstance(function_name, str):
        return function_name
    return type(function).__name__


def select_wrapper_metadata(
    function: Callable[..., object],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return wrapper assignments and updates safe for a function wrapper."""
    assigned: list[str] = []
    assignment_attributes: tuple[str, ...] = tuple(
        str(attribute) for attribute in WRAPPER_ASSIGNMENTS
    )
    for attribute in assignment_attributes:
        value: object = getattr(function, attribute, None)
        valid_assignment: bool
        if attribute in {"__module__", "__name__", "__qualname__"}:
            valid_assignment = isinstance(value, str)
        elif attribute == "__doc__":
            valid_assignment = value is None or isinstance(value, str)
        elif attribute == "__annotations__":
            valid_assignment = isinstance(value, dict)
        elif attribute == "__type_params__":
            valid_assignment = isinstance(value, tuple)
        else:
            valid_assignment = False

        if valid_assignment:
            assigned.append(attribute)

    updated: tuple[str, ...] = tuple(
        attribute
        for attribute in WRAPPER_UPDATES
        if isinstance(getattr(function, attribute, None), Mapping)
    )
    return tuple(assigned), updated


def _decorate(
    function: Callable[P, R],
    *,
    label: str | None,
    clock: Callable[[], float],
    reporter: Callable[[Timing], None],
) -> Callable[P, R]:
    timing_label: str = resolve_label(function, label)
    wrapper_metadata: tuple[tuple[str, ...], tuple[str, ...]] = select_wrapper_metadata(
        function
    )
    wrapper_assignments: tuple[str, ...] = wrapper_metadata[0]
    wrapper_updates: tuple[str, ...] = wrapper_metadata[1]

    def report(started_at: float, *, failed: bool) -> None:
        elapsed: float = clock() - started_at
        reporter(Timing(label=timing_label, elapsed=elapsed, failed=failed))

    @wraps(function, assigned=wrapper_assignments, updated=wrapper_updates)
    def tracked(*args: P.args, **kwargs: P.kwargs) -> R:
        started_at: float = clock()
        try:
            result: R = function(*args, **kwargs)
        except BaseException:
            try:
                report(started_at, failed=True)
            except BaseException:
                pass
            raise

        report(started_at, failed=False)
        return result

    return tracked


@overload
def track(
    function: Callable[P, R],
    /,
    *,
    label: str | None = None,
    clock: Callable[[], float] = perf_counter,
    reporter: Callable[[Timing], None] = print_timing,
) -> Callable[P, R]: ...


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

    if function is not None:
        return _decorate(
            function,
            label=label,
            clock=clock,
            reporter=reporter,
        )

    def decorate(target: Callable[P, R]) -> Callable[P, R]:
        return _decorate(
            target,
            label=label,
            clock=clock,
            reporter=reporter,
        )

    return decorate


if __name__ == "__main__":

    @track(label="slow function")
    def slow_function() -> None:
        from time import sleep

        sleep(0.5)

    slow_function()
