"""Tests for recursively typed tree node counting."""

from __future__ import annotations

import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import NoneType
from typing import get_type_hints

import pytest

from CH_09_documentation.exercise_03.solution_00 import (
    Tree,
    count_nodes,
    main,
)


def test_count_nodes_counts_every_nested_named_node() -> None:
    tree: Tree = {
        "docs": {
            "api": {},
            "guide": {"intro": {}},
        },
        "src": {
            "package": {
                "module": {},
            },
        },
    }

    assert count_nodes(tree) == 7


def test_count_nodes_returns_zero_for_empty_tree() -> None:
    tree: Tree = {}

    assert count_nodes(tree) == 0


def test_count_nodes_rejects_direct_cycle() -> None:
    tree: Tree = {}
    tree["self"] = tree

    with pytest.raises(ValueError, match=r"^tree contains cycle$"):
        count_nodes(tree)


def test_count_nodes_rejects_deep_cycle() -> None:
    tree: Tree = {"first": {"second": {"third": {}}}}
    third: Tree = tree["first"]["second"]["third"]
    third["back"] = tree["first"]

    with pytest.raises(ValueError, match=r"^tree contains cycle$"):
        count_nodes(tree)


def test_shared_acyclic_subtree_is_counted_per_occurrence() -> None:
    shared: Tree = {"leaf": {}}
    tree: Tree = {
        "left": shared,
        "right": shared,
    }

    assert count_nodes(tree) == 4


def test_count_nodes_does_not_mutate_input() -> None:
    tree: Tree = {
        "alpha": {"one": {}, "two": {}},
        "beta": {"three": {}},
    }
    before: Tree = deepcopy(tree)
    alpha: Tree = tree["alpha"]

    assert count_nodes(tree) == 5
    assert tree == before
    assert tree["alpha"] is alpha


def test_count_depends_on_structure_not_names_or_insertion_order() -> None:
    first: Tree = {
        "alpha": {"child": {}},
        "beta": {},
    }
    second: Tree = {
        "renamed-beta": {},
        "renamed-alpha": {"renamed-child": {}},
    }

    assert count_nodes(first) == 3
    assert count_nodes(second) == 3


def test_tree_alias_has_exact_recursive_shape() -> None:
    assert Tree == dict[str, "Tree"]


def test_function_annotations_are_exact() -> None:
    assert get_type_hints(count_nodes) == {
        "tree": Tree,
        "return": int,
    }
    assert get_type_hints(main) == {"return": NoneType}


def test_import_is_silent() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_09_documentation.exercise_03.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_module_prints_canonical_count() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "CH_09_documentation.exercise_03.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == "6\n"
    assert completed.stderr == ""
