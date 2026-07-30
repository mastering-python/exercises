"""Generate the infinite Fibonacci sequence."""

from collections.abc import Iterator
from itertools import islice


def fibonacci() -> Iterator[int]:
    """Yield ``0, 1, 1, 2, ...`` forever."""
    current: int = 0
    following: int = 1
    while True:
        yield current
        current, following = following, current + following


def main() -> None:
    """Print a bounded prefix of the infinite sequence."""
    numbers: list[int] = list(islice(fibonacci(), 10))
    print(numbers)


if __name__ == "__main__":
    main()
