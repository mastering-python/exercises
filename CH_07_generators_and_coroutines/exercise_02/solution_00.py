"""Expose non-negative slices over one consumable iterator."""

from __future__ import annotations

import itertools
from collections.abc import Iterable, Iterator
from typing import Generic, Protocol, TypeVar, cast

T = TypeVar("T")


class _SliceIndex(Protocol):
    @property
    def start(self) -> int | None: ...

    @property
    def stop(self) -> int | None: ...

    @property
    def step(self) -> int | None: ...


def _require_slice(index: object) -> _SliceIndex:
    """Return a slice or reject another runtime index type."""
    if not isinstance(index, slice):
        raise TypeError("SliceableGenerator accepts slices only")
    return cast(_SliceIndex, index)


class SliceableGenerator(Generic[T]):
    """Apply each slice relative to one iterator's current position."""

    def __init__(self, iterable: Iterable[T]) -> None:
        self._iterator: Iterator[T] = iter(iterable)

    def __getitem__(self, index: slice) -> list[T]:
        """Consume and return the requested non-negative forward slice."""
        normalized: _SliceIndex = _require_slice(index)
        start: int = 0 if normalized.start is None else normalized.start
        stop: int | None = normalized.stop
        step: int = 1 if normalized.step is None else normalized.step
        if start < 0 or (stop is not None and stop < 0):
            raise ValueError("slice bounds must be non-negative")
        if step <= 0:
            raise ValueError("slice step must be positive")
        return list(itertools.islice(self._iterator, start, stop, step))


def main() -> None:
    """Demonstrate a bounded slice from an infinite iterator."""
    generator: SliceableGenerator[int] = SliceableGenerator(itertools.count())
    values: list[int] = generator[10:20]
    print(values)


if __name__ == "__main__":
    main()
