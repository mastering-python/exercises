"""Implement the quicksort algorithm."""

from collections.abc import Iterable
from typing import Protocol, TypeVar, cast

T = TypeVar("T")
T_contra = TypeVar("T_contra", contravariant=True)


class _SupportsLessThan(Protocol[T_contra]):
    def __lt__(self, other: T_contra, /) -> bool: ...


def _quicksort(values: list[T]) -> list[T]:
    if len(values) <= 1:
        return values.copy()

    iterator = iter(values)
    pivot: T = next(iterator)
    lower: list[T] = []
    upper: list[T] = []
    for value in iterator:
        comparable: _SupportsLessThan[T] = cast(_SupportsLessThan[T], value)
        if comparable < pivot:
            lower.append(value)
        else:
            upper.append(value)

    return [*_quicksort(lower), pivot, *_quicksort(upper)]


def quicksort(values: Iterable[T]) -> list[T]:
    """Return the values in ascending order without mutating the input."""
    materialized: list[T] = list(values)
    return _quicksort(materialized)


def qs(values: Iterable[T]) -> list[T]:
    """Compatibility wrapper for the historical short function name."""
    return quicksort(values)


def main() -> None:
    values: list[int] = [8, 3, 5, 3, 1]
    expected: list[int] = [1, 3, 3, 5, 8]
    assert quicksort(values) == expected
    assert qs(values) == expected


if __name__ == "__main__":
    main()
