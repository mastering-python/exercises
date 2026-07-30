"""Tests for flattening explicitly typed nested measurements."""

import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import NoneType
from typing import get_type_hints

from CH_09_documentation.exercise_02.solution_00 import (
    NestedMeasurements,
    flatten_measurements,
    main,
)


def test_flatten_measurements_preserves_mapping_and_list_order() -> None:
    values: NestedMeasurements = {
        "north": [(2, 2.5), (1, 1.5)],
        "south": [(4, 4.5), (3, 3.5)],
    }

    assert flatten_measurements(values) == [2.5, 1.5, 4.5, 3.5]


def test_flatten_measurements_accepts_an_empty_mapping() -> None:
    values: NestedMeasurements = {}

    assert flatten_measurements(values) == []


def test_flatten_measurements_skips_empty_levels() -> None:
    values: NestedMeasurements = {
        "north": [],
        "south": [(3, 3.5)],
        "west": [],
    }

    assert flatten_measurements(values) == [3.5]


def test_flatten_measurements_preserves_duplicate_ids_and_values() -> None:
    values: NestedMeasurements = {
        "north": [(1, 1.5), (1, 1.5)],
        "south": [(1, 1.5)],
    }

    assert flatten_measurements(values) == [1.5, 1.5, 1.5]


def test_flatten_measurements_does_not_mutate_input() -> None:
    values: NestedMeasurements = {
        "north": [(1, 1.5), (2, 2.5)],
        "south": [(3, 3.5)],
    }
    before: NestedMeasurements = deepcopy(values)
    north_rows: list[tuple[int, float]] = values["north"]

    flattened: list[float] = flatten_measurements(values)

    assert flattened == [1.5, 2.5, 3.5]
    assert values == before
    assert values["north"] is north_rows


def test_nested_measurements_alias_has_exact_shape() -> None:
    assert NestedMeasurements == dict[str, list[tuple[int, float]]]


def test_function_annotations_are_exact() -> None:
    assert get_type_hints(flatten_measurements) == {
        "values": NestedMeasurements,
        "return": list[float],
    }
    assert get_type_hints(main) == {"return": NoneType}


def test_import_is_silent() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_09_documentation.exercise_02.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_module_prints_canonical_list() -> None:
    repository_root: Path = Path(__file__).parents[2]
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "CH_09_documentation.exercise_02.solution_00",
        ],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == "[1.5, 2.5]\n"
    assert completed.stderr == ""
