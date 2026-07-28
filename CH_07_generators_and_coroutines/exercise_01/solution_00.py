"""Slice iterables with support for negative steps."""

from collections.abc import Iterable, Iterator
from itertools import islice as stdlib_islice
from operator import index
from typing import TypeVar

T = TypeVar("T")


def islice(
    iterable: Iterable[T],
    start: int,
    stop: int,
    step: int = 1,
) -> Iterator[T]:
    """Return an iterator over the requested slice of *iterable*.

    Positive steps retain :func:`itertools.islice` streaming behavior.
    Negative steps first materialize the iterable, which must therefore be
    finite, and then apply ordinary list-slice semantics.
    """
    normalized_start: int = index(start)
    normalized_stop: int = index(stop)
    normalized_step: int = index(step)

    if normalized_step == 0:
        raise ValueError("step must not be zero")
    if normalized_step > 0:
        return stdlib_islice(
            iterable,
            normalized_start,
            normalized_stop,
            normalized_step,
        )

    values: list[T] = list(iterable)
    return iter(values[normalized_start:normalized_stop:normalized_step])


def main() -> None:
    """Demonstrate a negative-step iterable slice."""
    print(list(islice(range(30), 20, 10, -1)))


if __name__ == "__main__":
    main()
