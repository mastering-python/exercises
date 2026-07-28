"""Deterministic sequential and bounded spawn-process merge sort."""

from __future__ import annotations

import multiprocessing
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from multiprocessing.context import BaseContext
from typing import cast

__all__: list[str] = [
    "merge",
    "merge_sort",
    "multiprocessing_merge_sort",
    "parallel_merge_sort",
    "split",
]


def _validated_values(values: Sequence[int]) -> list[int]:
    raw_values: object = cast(object, values)
    if not isinstance(raw_values, Sequence):
        raise TypeError("values must be an integer sequence")
    candidate_values: Sequence[object] = cast(Sequence[object], raw_values)
    copied: list[int] = []
    value: object
    for value in candidate_values:
        if type(value) is not int:
            raise TypeError("values must contain only integers")
        copied.append(value)
    return copied


def merge(left: Sequence[int], right: Sequence[int]) -> list[int]:
    """Merge two sorted integer sequences without mutating either."""

    left_values: list[int] = _validated_values(left)
    right_values: list[int] = _validated_values(right)
    merged: list[int] = []
    left_index: int = 0
    right_index: int = 0
    while left_index < len(left_values) and right_index < len(right_values):
        if left_values[left_index] <= right_values[right_index]:
            merged.append(left_values[left_index])
            left_index += 1
        else:
            merged.append(right_values[right_index])
            right_index += 1
    merged.extend(left_values[left_index:])
    merged.extend(right_values[right_index:])
    return merged


def split(values: Sequence[int], size: int) -> list[list[int]]:
    """Split an integer sequence into at most ``size`` balanced chunks."""

    if type(size) is not int:
        raise TypeError("size must be an integer")
    if size < 1:
        raise ValueError("size must be positive")
    copied: list[int] = _validated_values(values)
    if not copied:
        return []
    chunk_count: int = min(size, len(copied))
    base_size, remainder = divmod(len(copied), chunk_count)
    chunks: list[list[int]] = []
    start: int = 0
    index: int
    for index in range(chunk_count):
        chunk_size: int = base_size + (1 if index < remainder else 0)
        stop: int = start + chunk_size
        chunks.append(copied[start:stop])
        start = stop
    return chunks


def _merge_sort_validated(values: list[int]) -> list[int]:
    if len(values) < 2:
        return values.copy()
    middle: int = len(values) // 2
    left: list[int] = _merge_sort_validated(values[:middle])
    right: list[int] = _merge_sort_validated(values[middle:])
    return merge(left, right)


def merge_sort(values: Sequence[int]) -> list[int]:
    """Return a non-mutating sequential merge sort."""

    return _merge_sort_validated(_validated_values(values))


def _merge_pair(pair: tuple[list[int], list[int]]) -> list[int]:
    left, right = pair
    return merge(left, right)


def parallel_merge_sort(
    values: Sequence[int],
    *,
    max_workers: int | None = None,
    context: BaseContext | None = None,
) -> list[int]:
    """Sort integers using bounded spawn-process map and pairwise merges."""

    if max_workers is not None:
        if type(max_workers) is not int:
            raise TypeError("max_workers must be an integer")
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
    copied: list[int] = _validated_values(values)
    if not copied:
        return []

    requested_workers: int = (
        max_workers if max_workers is not None else multiprocessing.cpu_count()
    )
    worker_count: int = min(requested_workers, len(copied))
    chunks: list[list[int]] = split(copied, worker_count)
    process_context: BaseContext = (
        context if context is not None else multiprocessing.get_context("spawn")
    )
    with ProcessPoolExecutor(
        max_workers=worker_count,
        mp_context=process_context,
    ) as executor:
        sorted_chunks: list[list[int]] = list(executor.map(merge_sort, chunks))
        while len(sorted_chunks) > 1:
            pairs: list[tuple[list[int], list[int]]] = list(
                zip(sorted_chunks[::2], sorted_chunks[1::2], strict=False)
            )
            merged: list[list[int]] = list(executor.map(_merge_pair, pairs))
            if len(sorted_chunks) % 2:
                merged.append(sorted_chunks[-1])
            sorted_chunks = merged
    return sorted_chunks[0]


def multiprocessing_merge_sort(values: Sequence[int]) -> list[int]:
    """Compatibility wrapper using bounded spawn-process merge sort."""

    return parallel_merge_sort(values)


def main() -> None:
    """Run a deterministic bounded parallel-sort demonstration."""

    values: list[int] = [9, 3, -1, 7, 3, 0]
    print(parallel_merge_sort(values, max_workers=2))


if __name__ == "__main__":
    main()
