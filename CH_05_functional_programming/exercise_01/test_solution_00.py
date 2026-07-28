from __future__ import annotations

import ast
from collections.abc import Iterator
from pathlib import Path
from typing import ClassVar

import pytest

from . import solution_00
from .solution_00 import qs, quicksort


class OneShotIterable:
    def __init__(self, values: list[int]) -> None:
        self._values: list[int] = values
        self._iterated: bool = False

    def __iter__(self) -> Iterator[int]:
        if self._iterated:
            raise AssertionError("iterable consumed more than once")
        self._iterated = True
        yield from self._values


class Record:
    def __init__(self, name: str, rank: int) -> None:
        self.name: str = name
        self.rank: int = rank

    def __lt__(self, other: Record) -> bool:
        return self.rank < other.rank


class CountedValue:
    comparisons: ClassVar[int] = 0

    def __init__(self, value: int) -> None:
        self.value: int = value

    def __lt__(self, other: CountedValue) -> bool:
        type(self).comparisons += 1
        return self.value < other.value


class BrokenComparison:
    def __lt__(self, other: BrokenComparison) -> bool:
        del other
        raise RuntimeError("comparison failed")


def test_quicksort_accepts_generator() -> None:
    values: Iterator[int] = (value for value in [4, 1, 3, 2])

    assert quicksort(values) == [1, 2, 3, 4]


def test_quicksort_consumes_one_shot_iterable_once() -> None:
    values: OneShotIterable = OneShotIterable([3, 1, 2])

    assert quicksort(values) == [1, 2, 3]


def test_quicksort_preserves_duplicate_values() -> None:
    assert quicksort([3, 1, 3, 2, 1, 3]) == [1, 1, 2, 3, 3, 3]


@pytest.mark.parametrize("values", [[], [42]])
def test_quicksort_returns_fresh_list_for_short_inputs(values: list[int]) -> None:
    result: list[int] = quicksort(values)

    assert result == values
    assert result is not values


def test_quicksort_does_not_mutate_input_list_or_records() -> None:
    high: Record = Record("high", 3)
    low: Record = Record("low", 1)
    middle: Record = Record("middle", 2)
    values: list[Record] = [high, low, middle]

    result: list[Record] = quicksort(values)

    assert values == [high, low, middle]
    assert [(record.name, record.rank) for record in values] == [
        ("high", 3),
        ("low", 1),
        ("middle", 2),
    ]
    assert result == [low, middle, high]


def test_quicksort_uses_only_less_than_and_preserves_equivalent_records() -> None:
    first: Record = Record("first", 2)
    lower: Record = Record("lower", 1)
    second: Record = Record("second", 2)
    third: Record = Record("third", 2)

    result: list[Record] = quicksort([first, lower, second, third])

    assert result == [lower, first, second, third]


@pytest.mark.parametrize(
    "raw_values",
    [
        list(range(12)),
        list(range(11, -1, -1)),
        [7] * 12,
    ],
)
def test_first_pivot_partition_compares_each_remaining_item_once(
    raw_values: list[int],
) -> None:
    values: list[CountedValue] = [CountedValue(value) for value in raw_values]
    CountedValue.comparisons = 0

    result: list[CountedValue] = quicksort(values)

    assert [value.value for value in result] == sorted(raw_values)
    assert CountedValue.comparisons == len(values) * (len(values) - 1) // 2


def test_qs_matches_quicksort() -> None:
    values: list[int] = [8, 3, 5, 3, 1]

    assert qs(iter(values)) == quicksort(values)


def test_comparison_errors_propagate() -> None:
    values: list[BrokenComparison] = [BrokenComparison(), BrokenComparison()]

    with pytest.raises(RuntimeError, match="comparison failed"):
        quicksort(values)


def test_module_demo_is_protected_by_main_guard() -> None:
    source_path: Path = Path(solution_00.__file__)
    module: ast.Module = ast.parse(source_path.read_text(encoding="utf-8"))
    guarded_calls: list[ast.Call] = [
        node
        for statement in module.body
        if isinstance(statement, ast.If)
        and isinstance(statement.test, ast.Compare)
        and isinstance(statement.test.left, ast.Name)
        and statement.test.left.id == "__name__"
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "main"
    ]

    assert guarded_calls
