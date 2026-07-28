"""Track function execution time with an injectable clock and reporter."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import WRAPPER_ASSIGNMENTS, WRAPPER_UPDATES, wraps
from time import perf_counter
from typing import ParamSpec, TypeVar, cast, overload

P = ParamSpec("P")
R = TypeVar("R")
_MISSING: object = object()


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


def snapshot_wrapper_metadata(
    function: Callable[..., object],
    label: str | None,
) -> tuple[str, dict[str, object], dict[str, object]]:
    """Snapshot a safe label, assigned metadata, and custom attributes."""

    def valid_assignment(attribute: str, value: object) -> bool:
        if attribute in {"__module__", "__name__", "__qualname__"}:
            return isinstance(value, str)
        if attribute == "__doc__":
            return value is None or isinstance(value, str)
        if attribute == "__annotations__":
            return isinstance(value, dict)
        if attribute == "__annotate__":
            return value is None or callable(value)
        if attribute == "__type_params__":
            return isinstance(value, tuple)
        return False

    def read_attribute(attribute: str) -> object:
        try:
            return getattr(function, attribute, _MISSING)
        except Exception:
            return _MISSING

    def callable_type_name() -> str:
        try:
            type_name: object = type.__getattribute__(
                type(function),
                "__name__",
            )
        except Exception:
            return "callable"
        if isinstance(type_name, str):
            return type_name
        return "callable"

    runtime_assignment_attributes: list[str] = [
        str(attribute) for attribute in WRAPPER_ASSIGNMENTS
    ]
    managed_attributes: tuple[str, ...] = (
        "__annotations__",
        "__annotate__",
        "__type_params__",
    )
    assignment_attributes_list: list[str] = [
        attribute
        for attribute in runtime_assignment_attributes
        if attribute not in managed_attributes
    ]
    assignment_attributes_list.extend(managed_attributes)
    assignment_attributes: tuple[str, ...] = tuple(assignment_attributes_list)
    reserved_attributes: set[str] = {
        *assignment_attributes,
        "__wrapped__",
    }

    function_name: object = read_attribute("__name__")
    timing_label: str
    if label is not None:
        timing_label = label
    elif isinstance(function_name, str):
        timing_label = function_name
    else:
        timing_label = callable_type_name()

    assigned: dict[str, object] = {}
    for attribute in assignment_attributes:
        value: object
        if attribute == "__name__":
            value = function_name
        else:
            value = read_attribute(attribute)
        if value is not _MISSING and valid_assignment(attribute, value):
            assigned[attribute] = value

    custom_attributes: dict[str, object] = {}
    for attribute in WRAPPER_UPDATES:
        source_updates: object = read_attribute(str(attribute))
        if not isinstance(source_updates, Mapping):
            continue
        source_mapping: Mapping[object, object] = cast(
            Mapping[object, object],
            source_updates,
        )
        for key, value in source_mapping.items():
            if isinstance(key, str) and key not in reserved_attributes:
                custom_attributes[key] = value

    return timing_label, assigned, custom_attributes


def _decorate(
    function: Callable[P, R],
    *,
    label: str | None,
    clock: Callable[[], float],
    reporter: Callable[[Timing], None],
) -> Callable[P, R]:
    wrapper_metadata: tuple[
        str,
        dict[str, object],
        dict[str, object],
    ] = snapshot_wrapper_metadata(function, label)
    timing_label: str = wrapper_metadata[0]
    assigned_metadata: dict[str, object] = wrapper_metadata[1]
    custom_attributes: dict[str, object] = wrapper_metadata[2]

    def report(started_at: float, *, failed: bool) -> None:
        elapsed: float = clock() - started_at
        reporter(Timing(label=timing_label, elapsed=elapsed, failed=failed))

    @wraps(function, assigned=(), updated=())
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

    tracked.__dict__.update(custom_attributes)
    for attribute, value in assigned_metadata.items():
        setattr(tracked, attribute, value)
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
