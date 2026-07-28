"""Slice iterables with support for negative steps."""

from collections.abc import Iterable, Iterator
from itertools import islice as stdlib_islice
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
    if step == 0:
        raise ValueError("step must not be zero")
    if step > 0:
        return stdlib_islice(iterable, start, stop, step)

    values: list[T] = list(iterable)
    return iter(values[start:stop:step])


def main() -> None:
    """Demonstrate a negative-step iterable slice."""
    print(list(islice(range(30), 20, 10, -1)))


if __name__ == "__main__":
    main()
