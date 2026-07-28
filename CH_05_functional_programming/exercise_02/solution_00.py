"""Group values without requiring adjacent equal keys."""

from collections.abc import Callable, Hashable, Iterable
from typing import TypeVar

T = TypeVar("T")
K = TypeVar("K", bound=Hashable)


def groupby(func: Callable[[T], K], seq: Iterable[T]) -> dict[K, list[T]]:
    """Group items by keys returned by ``func``, preserving encounter order."""
    if not callable(func):
        raise TypeError("func must be callable")

    groups: dict[K, list[T]] = {}
    for item in seq:
        key: K = func(item)
        groups.setdefault(key, []).append(item)
    return groups


def main() -> None:
    """Demonstrate grouping non-consecutive values."""
    values: list[int] = list(range(8))

    assert groupby(lambda value: value % 2, values) == {
        0: [0, 2, 4, 6],
        1: [1, 3, 5, 7],
    }


if __name__ == "__main__":
    main()
