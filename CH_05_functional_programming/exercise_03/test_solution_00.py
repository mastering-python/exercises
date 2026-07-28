from __future__ import annotations

import ast
import subprocess
import sys
from collections.abc import Callable, Hashable, Iterable, Iterator
from pathlib import Path
from typing import cast

import pytest

from . import solution_00
from .solution_00 import groupby

REPOSITORY_ROOT: Path = Path(__file__).resolve().parents[2]
MODULE_NAME: str = "CH_05_functional_programming.exercise_03.solution_00"


class OneShotIterable:
    def __init__(self, values: list[int]) -> None:
        self._values: Iterator[int] = iter(values)
        self._started: bool = False

    def __iter__(self) -> Iterator[int]:
        if self._started:
            raise AssertionError("iterable was restarted")
        self._started = True
        return self._values


class IterationForbidden:
    def __iter__(self) -> Iterator[int]:
        raise AssertionError("iterable was consumed")


class EqualKey:
    def __init__(self, label: str) -> None:
        self.label: str = label

    def __hash__(self) -> int:
        return 1

    def __eq__(self, other: object) -> bool:
        return isinstance(other, EqualKey)


class CollidingKey:
    def __init__(self, label: str) -> None:
        self.label: str = label

    def __hash__(self) -> int:
        return 1

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CollidingKey) and self.label == other.label


def test_groupby_identity_example_returns_lists() -> None:
    groups: dict[str, list[str]] = groupby("ABACA")

    assert groups == {"A": ["A", "A", "A"], "B": ["B"], "C": ["C"]}
    assert all(isinstance(group, list) for group in groups.values())


def test_group_lists_are_reusable_and_independent() -> None:
    groups: dict[str, list[str]] = groupby("ABACA")
    first_read: list[str] = list(groups["A"])
    second_read: list[str] = list(groups["A"])

    groups["A"].append("changed")

    assert first_read == second_read == ["A", "A", "A"]
    assert groups["B"] == ["B"]
    assert groups["A"] is not groups["B"]


def test_groupby_accepts_empty_generator() -> None:
    empty: Iterable[int] = ()
    values: Iterator[int] = (value for value in empty)

    assert groupby(values) == {}


def test_groupby_consumes_one_shot_iterable_once() -> None:
    values: OneShotIterable = OneShotIterable([3, 1, 2, 4])

    assert groupby(values, key=lambda value: value % 2) == {
        1: [3, 1],
        0: [2, 4],
    }


def test_groupby_identity_signature_preserves_types() -> None:
    groups: dict[str, list[str]] = groupby(["alpha", "beta", "alpha"])

    assert groups == {"alpha": ["alpha", "alpha"], "beta": ["beta"]}


def test_groupby_keyed_signature_preserves_item_and_key_types() -> None:
    groups: dict[int, list[str]] = groupby(["one", "three", "two"], key=len)

    assert groups == {3: ["one", "two"], 5: ["three"]}


def test_keyed_groupby_accepts_unhashable_items() -> None:
    values: list[list[int]] = [[1], [2, 3], [4]]

    assert groupby(values, key=len) == {1: [[1], [4]], 2: [[2, 3]]}


def test_noncallable_key_is_rejected_before_iterable_consumption() -> None:
    invalid_key: Callable[[int], int] = cast(Callable[[int], int], 0)

    with pytest.raises(TypeError, match=r"^key must be callable or None$"):
        groupby(IterationForbidden(), key=invalid_key)


def test_first_key_and_item_encounter_order_are_preserved() -> None:
    groups: dict[int, list[int]] = groupby(
        [5, 2, 3, 4, 1, 6], key=lambda value: value % 3
    )

    assert list(groups) == [2, 0, 1]
    assert groups == {2: [5, 2], 0: [3, 6], 1: [4, 1]}


def test_key_callback_is_called_once_per_item_in_encounter_order() -> None:
    calls: list[int] = []

    def recording_key(value: int) -> int:
        calls.append(value)
        return value % 2

    values: list[int] = [4, 1, 4, 3]

    assert groupby(values, key=recording_key) == {
        0: [4, 4],
        1: [1, 3],
    }
    assert calls == values


def test_key_callback_error_propagates_without_consuming_later_items() -> None:
    yielded: list[int] = []

    def values() -> Iterator[int]:
        for value in [1, 2, 3]:
            yielded.append(value)
            yield value

    def failing_key(value: int) -> int:
        if value == 2:
            raise RuntimeError("key failed")
        return value

    with pytest.raises(RuntimeError, match=r"^key failed$"):
        groupby(values(), key=failing_key)

    assert yielded == [1, 2]


def test_unhashable_identity_key_error_propagates() -> None:
    values: Iterable[Hashable] = cast(Iterable[Hashable], [[1]])

    with pytest.raises(TypeError, match="unhashable type"):
        groupby(values)


def test_unhashable_derived_key_error_propagates() -> None:
    def unhashable_key(value: int) -> Hashable:
        return cast(Hashable, [value])

    with pytest.raises(TypeError, match="unhashable type"):
        groupby([1], key=unhashable_key)


def test_groupby_does_not_modify_input_list() -> None:
    values: list[int] = [3, 1, 2, 3]
    original: list[int] = values.copy()

    groupby(values)

    assert values == original


def test_equal_keys_keep_first_encountered_key_object() -> None:
    first: EqualKey = EqualKey("first")
    second: EqualKey = EqualKey("second")

    groups: dict[EqualKey, list[str]] = groupby(
        ["alpha", "beta"], key=lambda value: first if value == "alpha" else second
    )
    retained_key: EqualKey = next(iter(groups))

    assert list(groups) == [first]
    assert retained_key is first
    assert groups[first] == ["alpha", "beta"]


def test_hash_collisions_keep_distinct_groups() -> None:
    first: CollidingKey = CollidingKey("first")
    second: CollidingKey = CollidingKey("second")

    groups: dict[CollidingKey, list[str]] = groupby(
        ["alpha", "beta"], key=lambda value: first if value == "alpha" else second
    )

    assert list(groups) == [first, second]
    assert groups[first] == ["alpha"]
    assert groups[second] == ["beta"]


def test_import_is_silent() -> None:
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-c", f"import {MODULE_NAME}"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""


def test_module_demo_has_exact_output() -> None:
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-m", MODULE_NAME],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ("{'A': ['A', 'A', 'A'], 'B': ['B'], 'C': ['C']}\n")
    assert result.stderr == ""


def test_module_demo_is_protected_by_exact_main_guard() -> None:
    source_path: Path = Path(solution_00.__file__)
    tree: ast.Module = ast.parse(source_path.read_text(encoding="utf-8"))
    final_statement: ast.stmt = tree.body[-1]

    assert isinstance(final_statement, ast.If)
    assert ast.dump(final_statement.test, include_attributes=False) == (
        "Compare(left=Name(id='__name__', ctx=Load()), ops=[Eq()], "
        "comparators=[Constant(value='__main__')])"
    )
    assert len(final_statement.body) == 1
    assert ast.dump(final_statement.body[0], include_attributes=False) == (
        "Expr(value=Call(func=Name(id='main', ctx=Load()), args=[], keywords=[]))"
    )
