from collections.abc import Collection, Iterator
from dataclasses import dataclass

import pytest

from .solution_00 import SortedList


def test_empty_collection() -> None:
    values: SortedList[int, int] = SortedList()

    assert isinstance(values, Collection)
    assert len(values) == 0
    assert list(values) == []
    assert values.tree_height == 0


def test_add_insert_and_duplicate_values() -> None:
    values: SortedList[int, int] = SortedList()

    values.add(3)
    values.insert(1)
    values.add(2)
    values.insert(2)

    assert list(values) == [1, 2, 2, 3]
    assert len(values) == 4


@pytest.mark.parametrize(
    "insertions",
    [
        [3, 2, 1],
        [3, 1, 2],
        [1, 2, 3],
        [1, 3, 2],
    ],
    ids=["LL", "LR", "RR", "RL"],
)
def test_three_node_insertions_apply_each_avl_rotation(
    insertions: list[int],
) -> None:
    values: SortedList[int, int] = SortedList(insertions)

    assert list(values) == [1, 2, 3]
    assert values.tree_height == 2


@pytest.mark.parametrize(
    "source", [range(1_024), range(1_023, -1, -1)], ids=["ascending", "descending"]
)
def test_monotonic_input_stays_balanced(source: range) -> None:
    values: SortedList[int, int] = SortedList(source)

    assert list(values) == list(range(1_024))
    assert len(values) == 1_024
    assert values.tree_height <= 20


def test_reverse_key_controls_order() -> None:
    values: SortedList[int, int] = SortedList([1, 3, 2], key=lambda value: -value)

    assert list(values) == [3, 2, 1]


@dataclass(frozen=True)
class _Record:
    group: int
    label: str


def test_equal_sort_keys_preserve_insertion_order_and_membership() -> None:
    alpha: _Record = _Record(1, "alpha")
    beta: _Record = _Record(1, "beta")
    gamma: _Record = _Record(2, "gamma")
    values: SortedList[_Record, int] = SortedList(
        [beta, gamma, alpha, beta], key=lambda record: record.group
    )

    assert list(values) == [beta, alpha, beta, gamma]
    assert beta in values
    assert _Record(1, "missing") not in values
    assert _Record(3, "missing") not in values


def test_repr_uses_sorted_iteration_order() -> None:
    values: SortedList[int, int] = SortedList([3, 1, 2, 2])

    assert repr(values) == "SortedList([1, 2, 2, 3])"


def test_constructor_consumes_one_shot_iterable_once() -> None:
    consumed: list[int] = []

    def source() -> Iterator[int]:
        for value in (3, 1, 2):
            consumed.append(value)
            yield value

    iterator: Iterator[int] = source()
    values: SortedList[int, int] = SortedList(iterator)

    assert consumed == [3, 1, 2]
    assert list(values) == [1, 2, 3]
    assert list(iterator) == []


def test_key_is_called_once_per_inserted_value() -> None:
    calls: list[str] = []

    def measured_key(value: str) -> int:
        calls.append(value)
        return len(value)

    values: SortedList[str, int] = SortedList(["bbb", "a"], key=measured_key)
    values.add("cc")
    values.insert("dddd")

    assert calls == ["bbb", "a", "cc", "dddd"]
    assert list(values) == ["a", "cc", "bbb", "dddd"]


def test_duplicate_mutations_change_count_without_changing_height() -> None:
    values: SortedList[int, int] = SortedList([2, 1, 3])
    original_height: int = values.tree_height

    values.add(2)
    values.insert(2)

    assert len(values) == 5
    assert values.tree_height == original_height
    assert list(values) == [1, 2, 2, 2, 3]
