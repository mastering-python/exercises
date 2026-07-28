"""Runtime parameter type checks with reusable numeric constraints."""

from __future__ import annotations

import inspect
import types
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from numbers import Real
from typing import (
    Annotated,
    Any,
    Literal,
    ParamSpec,
    Protocol,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

__all__: list[str] = [
    "Between",
    "Constraint",
    "GreaterThan",
    "Gt",
    "LessThan",
    "enforce_type_hints",
    "type_check",
]

P = ParamSpec("P")
R = TypeVar("R")


class Constraint(Protocol):
    """A named-argument validator used by :func:`type_check`."""

    def validate(self, name: str, value: object) -> None:
        """Raise when ``value`` does not satisfy the constraint."""


def _real_bound(value: object) -> Real:
    if not isinstance(value, Real):
        raise TypeError("constraint bounds must be real numbers")
    return value


def _real_value(name: str, value: object) -> Real:
    if not isinstance(value, Real):
        raise TypeError(f"{name}={value!r} must be a real number")
    return value


@dataclass(frozen=True)
class GreaterThan:
    """Require a real value strictly greater than ``value``."""

    value: object

    def __post_init__(self) -> None:
        _real_bound(self.value)

    def validate(self, name: str, value: object) -> None:
        bound: Real = _real_bound(self.value)
        numeric_value: Real = _real_value(name, value)
        if numeric_value <= bound:
            raise ValueError(
                f"{name}={value!r} must be greater than {self.value!r}",
            )


@dataclass(frozen=True)
class LessThan:
    """Require a real value strictly less than ``value``."""

    value: object

    def __post_init__(self) -> None:
        _real_bound(self.value)

    def validate(self, name: str, value: object) -> None:
        bound: Real = _real_bound(self.value)
        numeric_value: Real = _real_value(name, value)
        if numeric_value >= bound:
            raise ValueError(
                f"{name}={value!r} must be less than {self.value!r}",
            )


@dataclass(frozen=True)
class Between:
    """Require a real value between ordered lower and upper bounds."""

    lower: object
    upper: object
    inclusive: object = False

    def __post_init__(self) -> None:
        lower: Real = _real_bound(self.lower)
        upper: Real = _real_bound(self.upper)
        _inclusive_value(self.inclusive)
        if not lower < upper:
            raise ValueError("lower bound must be less than upper bound")

    def validate(self, name: str, value: object) -> None:
        lower: Real = _real_bound(self.lower)
        upper: Real = _real_bound(self.upper)
        numeric_value: Real = _real_value(name, value)
        if _inclusive_value(self.inclusive):
            valid: bool = lower <= numeric_value <= upper
            interval: str = "inclusive"
        else:
            valid = lower < numeric_value < upper
            interval = "exclusive"
        if not valid:
            raise ValueError(
                f"{name}={value!r} must be between "
                f"{self.lower!r} and {self.upper!r} ({interval})",
            )


def _annotation_name(annotation: object) -> str:
    if isinstance(annotation, type):
        return annotation.__name__
    return str(annotation).removeprefix("typing.")


def _inclusive_value(value: object) -> bool:
    if not isinstance(value, bool):
        raise TypeError("inclusive must be a bool")
    return value


def _matches_annotation(value: object, annotation: object) -> bool:
    if annotation is Any:
        return True
    if annotation is None:
        return value is None

    origin: Any = get_origin(annotation)
    arguments: tuple[object, ...] = get_args(annotation)
    if origin is Annotated:
        return _matches_annotation(value, arguments[0])
    if origin in (Union, types.UnionType):
        return any(_matches_annotation(value, member) for member in arguments)
    if origin is Literal:
        return value in arguments
    if isinstance(origin, type):
        return isinstance(value, origin)
    if isinstance(annotation, type):
        return isinstance(value, annotation)

    raise TypeError(
        f"unsupported runtime annotation: {_annotation_name(annotation)}",
    )


def _check_value(name: str, value: object, annotation: object) -> None:
    if not _matches_annotation(value, annotation):
        raise TypeError(
            f"{name} expected {_annotation_name(annotation)}, "
            f"got {type(value).__name__}",
        )


def _check_parameter(
    name: str,
    parameter: inspect.Parameter,
    value: object,
    annotation: object,
) -> None:
    if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
        for item in cast(tuple[object, ...], value):
            _check_value(name, item, annotation)
        return
    if parameter.kind is inspect.Parameter.VAR_KEYWORD:
        for item in cast(dict[str, object], value).values():
            _check_value(name, item, annotation)
        return
    _check_value(name, value, annotation)


def type_check(
    **constraints: Constraint,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Check annotated arguments and then apply named constraints."""

    configured_constraints: dict[str, Constraint] = dict(constraints)

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        signature: inspect.Signature = inspect.signature(function)
        for name, constraint in configured_constraints.items():
            if name not in signature.parameters:
                raise TypeError(f"unknown constrained parameter: {name!r}")
            if not callable(getattr(constraint, "validate", None)):
                raise TypeError(
                    f"constraint for {name!r} must provide "
                    "validate(name, value)",
                )

        annotations: dict[str, Any] = get_type_hints(function)

        @wraps(function)
        def checked(*args: P.args, **kwargs: P.kwargs) -> R:
            bound: inspect.BoundArguments = signature.bind(*args, **kwargs)
            bound.apply_defaults()

            for name, value in bound.arguments.items():
                annotation: object | None = annotations.get(name)
                if annotation is not None:
                    _check_parameter(
                        name,
                        signature.parameters[name],
                        value,
                        annotation,
                    )

            for name, constraint in configured_constraints.items():
                constraint.validate(name, bound.arguments[name])

            return function(*bound.args, **bound.kwargs)

        return checked

    return decorate


Gt = GreaterThan
enforce_type_hints = type_check


def _demonstrate() -> None:
    @type_check(bacon=Gt(0), eggs=Between(1, 4))
    def sandwich(bacon: float, eggs: int) -> str:
        return f"bacon: {bacon!r}, eggs: {eggs!r}"

    assert sandwich(1.5, 2) == "bacon: 1.5, eggs: 2"


if __name__ == "__main__":
    _demonstrate()
