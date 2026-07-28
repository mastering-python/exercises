"""Implement the quicksort algorithm."""

from collections.abc import Iterable
from typing import Any, Protocol, TypeVar, cast

T_contra = TypeVar("T_contra", contravariant=True)


class SupportsLessThan(Protocol[T_contra]):
    def __lt__(self, other: T_contra, /) -> bool: ...


class SupportsGreaterThan(Protocol[T_contra]):
    def __gt__(self, other: T_contra, /) -> bool: ...


T = TypeVar(
    "T",
    bound=SupportsLessThan[Any] | SupportsGreaterThan[Any],
)


def _quicksort(values: list[T]) -> list[T]:
    if len(values) <= 1:
        return values.copy()

    iterator = iter(values)
    pivot: T = next(iterator)
    lower: list[T] = []
    upper: list[T] = []
    for value in iterator:
        comparable: SupportsLessThan[Any] = cast(SupportsLessThan[Any], value)
        if comparable < pivot:
            lower.append(value)
        else:
            upper.append(value)

    return [*_quicksort(lower), pivot, *_quicksort(upper)]


def quicksort(values: Iterable[T]) -> list[T]:
    """Return a fresh sorted list after consuming the iterable once.

    Mutable input containers are not structurally modified, and the algorithm
    directly mutates no elements.
    """
    materialized: list[T] = list(values)
    return _quicksort(materialized)


def qs(values: Iterable[T]) -> list[T]:
    """Return a fresh sorted list after consuming the iterable once.

    Mutable input containers are not structurally modified, and this
    compatibility wrapper directly mutates no elements.
    """
    return quicksort(values)


def main() -> None:
    values: list[int] = [8, 3, 5, 3, 1]
    expected: list[int] = [1, 3, 3, 5, 8]
    assert quicksort(values) == expected
    assert qs(values) == expected


if __name__ == "__main__":
    main()
