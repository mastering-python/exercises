"""Memoize calls whose arguments can contain mutable built-in containers."""

from collections.abc import Callable, Hashable
from functools import wraps
from typing import ParamSpec, TypeAlias, TypeVar, cast

__all__: list[str] = ["cache", "memoize"]

_P = ParamSpec("_P")
_R = TypeVar("_R")

_CacheKey: TypeAlias = tuple[object, Hashable, Hashable]

cache: dict[_CacheKey, object] = {}
_MISSING: object = object()


def _freeze(value: object, active: set[int] | None = None) -> Hashable:
    """Return a type-tagged, hashable representation of an argument."""
    if active is None:
        active = set()

    value_type: type[object] = type(value)
    if not isinstance(value, (tuple, frozenset)) and isinstance(value, Hashable):
        return (value_type, value)

    if isinstance(value, (tuple, list, dict, set, frozenset)):
        container: object = cast(object, value)
        identity: int = id(container)
        if identity in active:
            raise ValueError("cyclic argument")
        active.add(identity)
        try:
            if isinstance(value, tuple):
                tuple_value: tuple[object, ...] = cast(tuple[object, ...], value)
                return (
                    value_type,
                    tuple(_freeze(item, active) for item in tuple_value),
                )
            if isinstance(value, list):
                list_value: list[object] = cast(list[object], value)
                return (
                    value_type,
                    tuple(_freeze(item, active) for item in list_value),
                )
            if isinstance(value, dict):
                dict_value: dict[object, object] = cast(dict[object, object], value)
                return (
                    value_type,
                    frozenset(
                        (_freeze(key, active), _freeze(item, active))
                        for key, item in dict_value.items()
                    ),
                )
            if isinstance(value, set):
                set_value: set[object] = cast(set[object], value)
                return (
                    value_type,
                    frozenset(_freeze(item, active) for item in set_value),
                )
            frozenset_value: frozenset[object] = cast(frozenset[object], value)
            return (
                value_type,
                frozenset(_freeze(item, active) for item in frozenset_value),
            )
        finally:
            active.remove(identity)

    raise TypeError(f"unsupported unhashable argument: {value_type.__name__}")


def memoize(function: Callable[_P, _R]) -> Callable[_P, _R]:
    """Cache successful calls by function and frozen arguments."""
    namespace: object = object()

    @wraps(function)
    def _memoize(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        key: _CacheKey = (namespace, _freeze(args), _freeze(kwargs))
        cached: object = cache.get(key, _MISSING)
        if cached is not _MISSING:
            return cast(_R, cached)

        result: _R = function(*args, **kwargs)
        cache[key] = result
        return result

    return _memoize
