"""Memoize each decorated callable with its own inspectable cache."""

from collections.abc import Callable, Hashable
from functools import wraps
from typing import ParamSpec, Protocol, TypeVar, cast

from CH_06_decorators.exercise_03.solution_00 import (
    _freeze,  # pyright: ignore[reportPrivateUsage]
)

__all__: list[str] = ["MemoizedCallable", "memoize"]

_P = ParamSpec("_P")
_R = TypeVar("_R")


class MemoizedCallable(Protocol[_P, _R]):
    """Callable interface exposed by :func:`memoize`."""

    __name__: str
    __doc__: str | None
    __wrapped__: Callable[_P, _R]

    @property
    def cache(self) -> dict[Hashable, _R]:
        """Return the callable's live cache."""
        ...

    def cache_clear(self) -> None:
        """Clear this callable's cache."""
        ...

    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        """Call the wrapped callable."""
        ...


class _CacheAttributes(Protocol[_R]):
    """Writable attributes attached to the wrapper."""

    cache: dict[Hashable, _R]
    cache_clear: Callable[[], None]


def memoize(function: Callable[_P, _R]) -> MemoizedCallable[_P, _R]:
    """Memoize *function* using a cache private to this decoration."""
    local_cache: dict[Hashable, _R] = {}
    missing: object = object()

    @wraps(function)
    def _memoized(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        key: Hashable = (_freeze(args), _freeze(kwargs))
        cached: object = local_cache.get(key, missing)
        if cached is not missing:
            return cast(_R, cached)

        result: _R = function(*args, **kwargs)
        local_cache[key] = result
        return result

    attributes: _CacheAttributes[_R] = cast(
        _CacheAttributes[_R],
        _memoized,
    )
    attributes.cache = local_cache
    attributes.cache_clear = local_cache.clear
    return cast(MemoizedCallable[_P, _R], _memoized)


@memoize
def printer(*args: object) -> None:
    """Print arguments once per distinct call."""
    print(args)


def main() -> None:
    """Run a small memoization demonstration."""
    printer("a", "b", "c")
    printer({"a": 1, "b": 2, "c": 3})


if __name__ == "__main__":
    main()
