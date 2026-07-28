"""Runtime parameter type checks with reusable numeric constraints."""

from __future__ import annotations

import inspect
import types
from _thread import LockType
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from math import isfinite
from numbers import Real
from threading import Lock
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
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError("constraint bounds must be real numbers")
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("constraint bounds must be finite real numbers")
    return value


def _real_value(name: str, value: object) -> Real:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name}={value!r} must be a real number")
    if isinstance(value, float) and not isfinite(value):
        raise ValueError(f"{name}={value!r} must be a finite real number")
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
        return any(
            type(value) is type(literal) and value == literal for literal in arguments
        )
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


def _function_globals(
    function: Callable[..., object],
) -> dict[str, Any] | None:
    candidate_globals: object = getattr(function, "__globals__", None)
    if not isinstance(candidate_globals, dict):
        return None
    return cast(dict[str, Any], candidate_globals)


def _declared_owner_namespace(
    function: Callable[..., object],
    signature: inspect.Signature,
    defining_locals: dict[str, Any],
    bound: inspect.BoundArguments,
) -> dict[str, Any] | None:
    function_module: object = getattr(function, "__module__", None)
    function_qualname: object = getattr(function, "__qualname__", None)
    if not isinstance(function_module, str) or not isinstance(
        function_qualname,
        str,
    ):
        return None

    owner_qualname, separator, attribute_name = function_qualname.rpartition(".")
    if not separator:
        return None
    owner_name: str = owner_qualname.rpartition(".")[2]
    if not owner_name or owner_name == "<locals>":
        return None

    global_namespace: dict[str, Any] | None = _function_globals(function)
    if owner_name in defining_locals or (
        global_namespace is not None and owner_name in global_namespace
    ):
        return None

    parameter_names: tuple[str, ...] = tuple(signature.parameters)
    if not parameter_names:
        return None
    receiver: object | None = bound.arguments.get(parameter_names[0])
    if receiver is None:
        return None
    receiver_type: type[object] = (
        cast(type[object], receiver) if isinstance(receiver, type) else type(receiver)
    )
    receiver_mro: tuple[type[object], ...] = cast(
        tuple[type[object], ...],
        type.__getattribute__(receiver_type, "__mro__"),
    )

    for candidate_owner in receiver_mro:
        candidate_module: object = type.__getattribute__(
            candidate_owner,
            "__module__",
        )
        candidate_qualname: object = type.__getattribute__(
            candidate_owner,
            "__qualname__",
        )
        if candidate_module != function_module or candidate_qualname != owner_qualname:
            continue
        try:
            descriptor: object = inspect.getattr_static(
                candidate_owner,
                attribute_name,
            )
        except AttributeError:
            continue
        target: object = descriptor
        if isinstance(descriptor, (classmethod, staticmethod)):
            descriptor_object: object = cast(object, descriptor)
            target = cast(
                object,
                object.__getattribute__(descriptor_object, "__func__"),
            )
        if not callable(target):
            continue
        try:
            original: Callable[..., object] = inspect.unwrap(target)
        except ValueError:
            continue
        if original is function:
            return {owner_name: candidate_owner}
    return None


def _resolve_parameter_annotations(
    function: Callable[..., object],
    signature: inspect.Signature,
    local_namespace: dict[str, Any],
) -> dict[str, Any]:
    raw_annotations: dict[str, object] = cast(
        dict[str, object],
        getattr(function, "__annotations__", {}),
    )
    parameter_annotations: dict[str, object] = {
        name: raw_annotations[name]
        for name in signature.parameters
        if name in raw_annotations
    }

    def annotation_target() -> None:
        pass

    annotation_target.__annotations__ = parameter_annotations
    global_namespace: dict[str, Any] | None = _function_globals(function)
    return get_type_hints(
        annotation_target,
        globalns=global_namespace,
        localns=local_namespace,
    )


def type_check(
    **constraints: Constraint,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Check annotated arguments and then apply named constraints."""

    configured_constraints: dict[str, Constraint] = dict(constraints)

    def decorate(function: Callable[P, R]) -> Callable[P, R]:
        signature: inspect.Signature = inspect.signature(function)
        current_frame: types.FrameType | None = inspect.currentframe()
        try:
            caller_frame: types.FrameType | None = (
                current_frame.f_back if current_frame is not None else None
            )
            defining_locals: dict[str, Any] = (
                dict(caller_frame.f_locals) if caller_frame is not None else {}
            )
        finally:
            del current_frame

        for name, constraint in configured_constraints.items():
            if name not in signature.parameters:
                raise TypeError(f"unknown constrained parameter: {name!r}")
            parameter: inspect.Parameter = signature.parameters[name]
            if parameter.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                raise TypeError(
                    f"constraint for variadic parameter {name!r} is not supported",
                )
            if not callable(getattr(constraint, "validate", None)):
                raise TypeError(
                    f"constraint for {name!r} must provide validate(name, value)",
                )

        annotations_cache: dict[str, Any] | None = None
        resolution_lock: LockType = Lock()

        def resolve_annotations(
            bound: inspect.BoundArguments,
        ) -> dict[str, Any]:
            nonlocal annotations_cache
            with resolution_lock:
                if annotations_cache is None:
                    try:
                        resolved: dict[str, Any] = _resolve_parameter_annotations(
                            function,
                            signature,
                            defining_locals,
                        )
                    except NameError:
                        owner_namespace: dict[str, Any] | None = (
                            _declared_owner_namespace(
                                function,
                                signature,
                                defining_locals,
                                bound,
                            )
                        )
                        if owner_namespace is None:
                            raise
                        local_namespace: dict[str, Any] = dict(defining_locals)
                        local_namespace.update(owner_namespace)
                        resolved = _resolve_parameter_annotations(
                            function,
                            signature,
                            local_namespace,
                        )
                    annotations_cache = resolved
                return annotations_cache

        @wraps(function)
        def checked(*args: P.args, **kwargs: P.kwargs) -> R:
            bound: inspect.BoundArguments = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            annotations: dict[str, Any] = resolve_annotations(bound)

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
