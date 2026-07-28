"""Configurable exact-type dispatch across one or more arguments."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from functools import wraps
from typing import (
    Any,
    ParamSpec,
    Protocol,
    TypeVar,
    cast,
    get_origin,
    get_type_hints,
)

__all__: list[str] = ["Dispatcher", "fancysingledispatch"]

P = ParamSpec("P")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., object])


class Dispatcher(Protocol[P, R]):
    """Callable returned by :func:`fancysingledispatch`."""

    __name__: str
    __doc__: str | None
    __wrapped__: Callable[P, R]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R: ...

    def register(self, function: F, /) -> F: ...


def _validated_names(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{label} must be a tuple of parameter names")
    names: tuple[object, ...] = cast(tuple[object, ...], value)
    for name in names:
        if not isinstance(name, str):
            raise TypeError(f"{label} parameter names must be strings")
    return cast(tuple[str, ...], names)


def _duplicate_name(names: tuple[str, ...]) -> str | None:
    seen: set[str] = set()
    for name in names:
        if name in seen:
            return name
        seen.add(name)
    return None


def _parameter_shape(
    signature: inspect.Signature,
) -> tuple[tuple[str, str], ...]:
    return tuple(
        (name, str(parameter.kind)) for name, parameter in signature.parameters.items()
    )


def fancysingledispatch(
    *ignored: str,
    dispatch_on: tuple[str, ...] | None = None,
    **ignored_by_name: bool,
) -> Callable[[Callable[P, R]], Dispatcher[P, R]]:
    """Build an exact-type dispatcher over selected function parameters.

    Without ``dispatch_on``, every base parameter participates except names
    excluded by the two legacy ignored-name forms. Registering the same type
    tuple again replaces its previous implementation.
    """

    validated_ignored: tuple[str, ...] = _validated_names(ignored, "ignored")
    ignored_keyword_names: tuple[str, ...] = tuple(ignored_by_name)
    for name, enabled in ignored_by_name.items():
        if enabled is not True:
            raise TypeError(f"ignored keyword {name!r} must be True")

    all_ignored: tuple[str, ...] = validated_ignored + ignored_keyword_names
    duplicate_ignored: str | None = _duplicate_name(all_ignored)
    if duplicate_ignored is not None:
        raise TypeError(
            f"duplicate ignored parameter name: {duplicate_ignored!r}",
        )

    if dispatch_on is not None:
        if all_ignored:
            raise TypeError(
                "dispatch_on cannot be combined with ignored parameter names",
            )
        selected_configuration: tuple[str, ...] = _validated_names(
            dispatch_on,
            "dispatch_on",
        )
        if not selected_configuration:
            raise TypeError(
                "dispatch_on must contain at least one parameter name",
            )
        duplicate_selected: str | None = _duplicate_name(
            selected_configuration,
        )
        if duplicate_selected is not None:
            raise TypeError(
                f"duplicate dispatch parameter name: {duplicate_selected!r}",
            )

    def decorate(base: Callable[P, R]) -> Dispatcher[P, R]:
        base_signature: inspect.Signature = inspect.signature(base)
        parameter_names: tuple[str, ...] = tuple(base_signature.parameters)

        for name in all_ignored:
            if name not in base_signature.parameters:
                raise TypeError(f"unknown ignored parameter name: {name!r}")

        if dispatch_on is None:
            ignored_names: frozenset[str] = frozenset(all_ignored)
            selected_names: tuple[str, ...] = tuple(
                name for name in parameter_names if name not in ignored_names
            )
        else:
            for name in dispatch_on:
                if name not in base_signature.parameters:
                    raise TypeError(
                        f"unknown dispatch parameter name: {name!r}",
                    )
            selected_names = dispatch_on

        base_shape: tuple[tuple[str, str], ...] = _parameter_shape(
            base_signature,
        )
        registry: dict[tuple[type[object], ...], Callable[..., R]] = {}

        def register(function: F) -> F:
            implementation_signature: inspect.Signature = inspect.signature(
                function,
            )
            if _parameter_shape(implementation_signature) != base_shape:
                raise TypeError(
                    "registered function parameters must match base names and kinds",
                )

            try:
                annotations: dict[str, object] = get_type_hints(function)
            except (NameError, SyntaxError, TypeError) as error:
                raise TypeError(
                    f"dispatch parameter annotations could not be resolved: {error}",
                ) from error

            key_parts: list[type[object]] = []
            for name in selected_names:
                annotation: object | None = annotations.get(name)
                if (
                    annotation is None
                    or annotation is Any
                    or get_origin(annotation) is not None
                    or not isinstance(annotation, type)
                ):
                    description: str = (
                        "missing" if annotation is None else str(annotation)
                    )
                    raise TypeError(
                        f"dispatch parameter {name!r} must have a resolvable "
                        "concrete class annotation; "
                        f"got {description}",
                    )
                key_parts.append(annotation)

            registry[tuple(key_parts)] = cast(Callable[..., R], function)
            return function

        @wraps(base)
        def dispatcher(*args: P.args, **kwargs: P.kwargs) -> R:
            bound: inspect.BoundArguments = base_signature.bind(*args, **kwargs)
            bound.apply_defaults()
            key: tuple[type[object], ...] = tuple(
                type(cast(object, bound.arguments[name])) for name in selected_names
            )
            implementation: Callable[..., R] = registry.get(key, base)
            return implementation(*args, **kwargs)

        vars(dispatcher)["register"] = register
        return cast(Dispatcher[P, R], dispatcher)

    return decorate


def _demonstrate() -> None:
    @fancysingledispatch(dispatch_on=("value", "unit"))
    def format_measurement(value: object, unit: object) -> str:
        return f"{value!r} {unit!r}"

    @format_measurement.register
    def _format_number(value: float, unit: str) -> str:
        return f"{value:g} {unit}"

    assert callable(_format_number)
    assert format_measurement(1.5, "m") == "1.5 m"
    assert format_measurement(1, "m") == "1 'm'"


if __name__ == "__main__":
    _demonstrate()
