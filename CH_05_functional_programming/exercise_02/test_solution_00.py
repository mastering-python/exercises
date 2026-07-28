from __future__ import annotations

import ast
import subprocess
import sys
from collections.abc import Callable, Hashable, Iterator
from pathlib import Path
from textwrap import dedent
from typing import cast

import pytest

from . import solution_00
from .solution_00 import groupby

REPOSITORY_ROOT: Path = Path(__file__).resolve().parents[2]
MODULE_NAME: str = "CH_05_functional_programming.exercise_02.solution_00"


class OneShotIterable:
    def __init__(self, values: list[int]) -> None:
        self._values: list[int] = values
        self._iterated: bool = False

    def __iter__(self) -> Iterator[int]:
        if self._iterated:
            raise AssertionError("iterable consumed more than once")
        self._iterated = True
        yield from self._values


class IterationForbidden:
    def __iter__(self) -> Iterator[int]:
        raise AssertionError("seq was consumed")


class TrackedIterable:
    def __init__(self, values: list[int]) -> None:
        self._values: list[int] = values
        self.yielded: list[int] = []

    def __iter__(self) -> Iterator[int]:
        for value in self._values:
            self.yielded.append(value)
            yield value


class Parity:
    def __call__(self, value: int) -> str:
        return "even" if value % 2 == 0 else "odd"


class CollidingEqualKey:
    def __init__(self, label: str, group: int) -> None:
        self.label: str = label
        self.group: int = group

    def __hash__(self) -> int:
        return 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CollidingEqualKey):
            return NotImplemented
        return self.group == other.group


class ExplodingEqualityKey:
    def __hash__(self) -> int:
        return 1

    def __eq__(self, other: object) -> bool:
        raise RuntimeError("key equality failed")


def run_type_checker(
    checker: str, probe_path: Path
) -> subprocess.CompletedProcess[str]:
    arguments: list[str]
    if checker == "mypy":
        arguments = [
            sys.executable,
            "-m",
            "mypy",
            "--strict",
            "--python-version",
            "3.10",
            str(probe_path),
        ]
    else:
        arguments = [
            sys.executable,
            "-m",
            "pyright",
            "--pythonversion",
            "3.10",
            str(probe_path),
        ]

    return subprocess.run(
        arguments,
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_groupby_combines_nonconsecutive_equal_parity_keys() -> None:
    result: dict[int, list[int]] = groupby(lambda value: value % 2, range(8))

    assert result == {0: [0, 2, 4, 6], 1: [1, 3, 5, 7]}
    assert type(result) is dict


def test_groupby_returns_empty_dict_for_empty_iterable() -> None:
    result: dict[int, list[int]] = groupby(lambda value: value, [])

    assert result == {}
    assert type(result) is dict


def test_groupby_consumes_one_shot_iterable_once() -> None:
    values: OneShotIterable = OneShotIterable([3, 1, 2, 4])

    assert groupby(lambda value: value % 2, values) == {
        1: [3, 1],
        0: [2, 4],
    }


def test_groupby_streams_and_exhausts_generator_expression_once() -> None:
    events: list[str] = []
    source: list[int] = [1, 2, 3, 4]

    def transform(value: int) -> int:
        events.append(f"transform:{value}")
        return value * 10

    def parity(value: int) -> int:
        events.append(f"key:{value}")
        return (value // 10) % 2

    values: Iterator[int] = (transform(value) for value in source)

    assert groupby(parity, values) == {1: [10, 30], 0: [20, 40]}
    assert events == [
        "transform:1",
        "key:10",
        "transform:2",
        "key:20",
        "transform:3",
        "key:30",
        "transform:4",
        "key:40",
    ]
    assert list(values) == []


def test_groupby_preserves_first_key_and_item_encounter_order() -> None:
    values: Iterator[str] = iter(["beta", "a", "bravo", "cat", "amber"])

    result: dict[str, list[str]] = groupby(lambda value: value[0], values)

    assert list(result) == ["b", "a", "c"]
    assert result == {
        "b": ["beta", "bravo"],
        "a": ["a", "amber"],
        "c": ["cat"],
    }


def test_groupby_calls_key_function_exactly_once_per_item() -> None:
    calls: list[int] = []

    def recording_key(value: int) -> int:
        calls.append(value)
        return value % 2

    values: list[int] = [4, 1, 4, 3]

    assert groupby(recording_key, values) == {0: [4, 4], 1: [1, 3]}
    assert calls == values


def test_groupby_accepts_callable_object() -> None:
    assert groupby(Parity(), [1, 2, 3]) == {
        "odd": [1, 3],
        "even": [2],
    }


def test_groupby_rejects_non_callable_before_consuming_seq() -> None:
    invalid_func: Callable[[int], int] = cast(Callable[[int], int], None)

    with pytest.raises(TypeError, match=r"^func must be callable$"):
        groupby(invalid_func, IterationForbidden())


def test_groupby_propagates_key_function_exception() -> None:
    expected_error: RuntimeError = RuntimeError("key failed")

    def broken_key(value: int) -> int:
        if value == 2:
            raise expected_error
        return value

    with pytest.raises(RuntimeError, match=r"^key failed$") as raised:
        groupby(broken_key, [1, 2, 3])

    assert raised.value is expected_error


def test_groupby_propagates_unhashable_key_error() -> None:
    def unhashable_key(value: int) -> Hashable:
        return cast(Hashable, [value])

    with pytest.raises(TypeError, match=r"unhashable type: 'list'"):
        groupby(unhashable_key, [1])


def test_groupby_merges_equal_colliding_keys_and_retains_first_key_object() -> None:
    first: CollidingEqualKey = CollidingEqualKey("first", 1)
    collision: CollidingEqualKey = CollidingEqualKey("collision", 2)
    equal_later: CollidingEqualKey = CollidingEqualKey("equal later", 1)

    result: dict[CollidingEqualKey, list[CollidingEqualKey]] = groupby(
        lambda key: key,
        [first, collision, equal_later],
    )

    result_keys: list[CollidingEqualKey] = list(result)
    assert result_keys == [first, collision]
    assert result_keys[0] is first
    assert result[first] == [first, equal_later]
    assert result[collision] == [collision]


def test_groupby_propagates_key_equality_error_without_further_consumption() -> None:
    values: TrackedIterable = TrackedIterable([1, 2, 3])
    calls: list[int] = []
    keys: dict[int, ExplodingEqualityKey] = {
        1: ExplodingEqualityKey(),
        2: ExplodingEqualityKey(),
        3: ExplodingEqualityKey(),
    }

    def broken_key(value: int) -> ExplodingEqualityKey:
        calls.append(value)
        return keys[value]

    with pytest.raises(RuntimeError, match=r"^key equality failed$"):
        groupby(broken_key, values)

    assert values.yielded == [1, 2]
    assert calls == [1, 2]


def test_groupby_does_not_structurally_mutate_input_container() -> None:
    values: list[str] = ["pear", "fig", "plum", "kiwi"]
    original: list[str] = values.copy()

    result: dict[int, list[str]] = groupby(len, values)

    assert values == original
    assert result == {4: ["pear", "plum", "kiwi"], 3: ["fig"]}


@pytest.mark.parametrize("checker", ["mypy", "pyright"])
def test_static_typing_rejects_unhashable_key_function(
    checker: str,
    tmp_path: Path,
) -> None:
    probe_path: Path = tmp_path / "invalid_groupby_typing.py"
    probe_path.write_text(
        dedent(
            """
            # pyright: strict
            from CH_05_functional_programming.exercise_02.solution_00 import groupby

            invalid = groupby(lambda value: [value], [1, 2])
            """
        ),
        encoding="utf-8",
    )

    result: subprocess.CompletedProcess[str] = run_type_checker(checker, probe_path)
    output: str = result.stdout + result.stderr

    assert result.returncode != 0, output
    assert "list[int]" in output


def test_import_is_quiet() -> None:
    import_result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-c", f"import {MODULE_NAME}"],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert import_result.returncode == 0, import_result.stderr
    assert import_result.stdout == ""
    assert import_result.stderr == ""


def test_module_demo_runs_under_exact_main_guard() -> None:
    execution_result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-m", MODULE_NAME],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert execution_result.returncode == 0, execution_result.stderr
    assert execution_result.stdout == ""
    assert execution_result.stderr == ""

    source_path: Path = Path(solution_00.__file__)
    module: ast.Module = ast.parse(source_path.read_text(encoding="utf-8"))
    exact_main_guards: list[ast.If] = [
        statement
        for statement in module.body
        if isinstance(statement, ast.If)
        and isinstance(statement.test, ast.Compare)
        and isinstance(statement.test.left, ast.Name)
        and statement.test.left.id == "__name__"
        and len(statement.test.ops) == 1
        and isinstance(statement.test.ops[0], ast.Eq)
        and len(statement.test.comparators) == 1
        and isinstance(statement.test.comparators[0], ast.Constant)
        and statement.test.comparators[0].value == "__main__"
    ]
    guarded_main_calls: list[ast.Call] = [
        node
        for statement in exact_main_guards
        for node in ast.walk(statement)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "main"
    ]

    assert len(exact_main_guards) == 1
    assert guarded_main_calls
