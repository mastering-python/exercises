"""Track function execution time with an injectable clock and reporter."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import WRAPPER_ASSIGNMENTS, WRAPPER_UPDATES, wraps
from time import perf_counter
from typing import ParamSpec, TypeVar, cast, overload

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
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, object]]:
    """Return safe wrapper assignments, updates, and filtered attributes."""

    def valid_assignment(attribute: str, value: object) -> bool:
        if attribute in {"__module__", "__name__", "__qualname__"}:
            return isinstance(value, str)
        if attribute == "__doc__":
            return value is None or isinstance(value, str)
        if attribute == "__annotations__":
            return isinstance(value, dict)
        if attribute == "__type_params__":
            return isinstance(value, tuple)
        return False

    assignment_attributes_list: list[str] = [
        str(attribute) for attribute in WRAPPER_ASSIGNMENTS
    ]
    if "__type_params__" not in assignment_attributes_list:
        assignment_attributes_list.append("__type_params__")
    assignment_attributes: tuple[str, ...] = tuple(assignment_attributes_list)
    reserved_attributes: set[str] = {
        *assignment_attributes,
        "__wrapped__",
    }

    assigned: list[str] = []
    for attribute in assignment_attributes:
        value: object = getattr(function, attribute, None)
        if valid_assignment(attribute, value):
            assigned.append(attribute)

    updated: list[str] = []
    filtered_attributes: dict[str, object] = {}
    for attribute in WRAPPER_UPDATES:
        source_updates: object = getattr(function, attribute, None)
        if not isinstance(source_updates, Mapping):
            continue
        source_mapping: Mapping[object, object] = cast(
            Mapping[object, object],
            source_updates,
        )
        has_invalid_metadata: bool = any(
            isinstance(key, str)
            and key in assignment_attributes
            and not valid_assignment(key, value)
            for key, value in source_mapping.items()
        )
        if not has_invalid_metadata:
            updated.append(attribute)
            continue

        for key, value in source_mapping.items():
            if isinstance(key, str) and key not in reserved_attributes:
                filtered_attributes[key] = value

    return tuple(assigned), tuple(updated), filtered_attributes


def _decorate(
    function: Callable[P, R],
    *,
    label: str | None,
    clock: Callable[[], float],
    reporter: Callable[[Timing], None],
) -> Callable[P, R]:
    timing_label: str = resolve_label(function, label)
    wrapper_metadata: tuple[
        tuple[str, ...],
        tuple[str, ...],
        dict[str, object],
    ] = select_wrapper_metadata(function)
    wrapper_assignments: tuple[str, ...] = wrapper_metadata[0]
    wrapper_updates: tuple[str, ...] = wrapper_metadata[1]
    filtered_attributes: dict[str, object] = wrapper_metadata[2]

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

    tracked.__dict__.update(filtered_attributes)
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
