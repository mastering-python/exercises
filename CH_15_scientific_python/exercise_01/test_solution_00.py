"""Tests for deterministic Datashader plotting."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pandas as pd  # type: ignore[import-untyped]
import pytest

from .solution_00 import aggregate_points, load_points, render_points, save_plot

FIXTURE: Path = Path(__file__).with_name("points.csv")
EXPECTED_FIXTURE: str = """x,y,category
-1.0,-1.0,a
-0.5,0.5,a
0.0,0.0,b
0.5,-0.5,b
1.0,1.0,c
1.0,1.0,c
"""


def test_fixture_and_loaded_points_are_exact() -> None:
    assert FIXTURE.read_text(encoding="utf-8") == EXPECTED_FIXTURE

    frame: pd.DataFrame = load_points(FIXTURE)

    assert list(frame.columns) == ["x", "y", "category"]
    assert frame.shape == (6, 3)
    x_values: list[float] = cast(
        list[float],
        frame["x"].tolist(),  # pyright: ignore[reportUnknownMemberType]
    )
    y_values: list[float] = cast(
        list[float],
        frame["y"].tolist(),  # pyright: ignore[reportUnknownMemberType]
    )
    categories: list[str] = cast(
        list[str],
        frame["category"].tolist(),  # pyright: ignore[reportUnknownMemberType]
    )
    assert x_values == [-1.0, -0.5, 0.0, 0.5, 1.0, 1.0]
    assert y_values == [-1.0, 0.5, 0.0, -0.5, 1.0, 1.0]
    assert categories == ["a", "a", "b", "b", "c", "c"]


def test_aggregate_uses_fixed_shape_and_counts_every_point() -> None:
    frame: pd.DataFrame = load_points(FIXTURE)

    aggregate = aggregate_points(frame, width=8, height=6)

    assert aggregate.shape == (6, 8)
    assert int(aggregate.sum()) == 6
    assert int(aggregate.max()) == 2


def test_render_is_deterministic() -> None:
    frame: pd.DataFrame = load_points(FIXTURE)

    first = render_points(frame, width=16, height=12).to_pil()
    second = render_points(frame, width=16, height=12).to_pil()

    assert first.size == (16, 12)
    assert first.tobytes() == second.tobytes()


def test_save_plot_creates_parent_directories_and_writes_png(tmp_path: Path) -> None:
    destination: Path = tmp_path / "nested" / "plot.png"

    result: Path = save_plot(FIXTURE, destination, width=16, height=12)

    assert result == destination
    assert destination.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize(
    ("width", "height"),
    [(0, 8), (8, 0), (-1, 8)],
)
def test_dimensions_must_be_positive(width: int, height: int) -> None:
    frame: pd.DataFrame = load_points(FIXTURE)

    with pytest.raises(ValueError, match=r"^plot dimensions must be positive$"):
        aggregate_points(frame, width=width, height=height)


def test_load_points_rejects_wrong_columns(tmp_path: Path) -> None:
    source: Path = tmp_path / "wrong.csv"
    source.write_text("x,y,label\n1,2,a\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"^point data must contain exactly x, y, category columns$",
    ):
        load_points(source)


def test_load_points_rejects_empty_data(tmp_path: Path) -> None:
    source: Path = tmp_path / "empty.csv"
    source.write_text("x,y,category\n", encoding="utf-8")

    with pytest.raises(ValueError, match=r"^point data must not be empty$"):
        load_points(source)


@pytest.mark.parametrize(
    "row",
    [
        "NaN,0,a",
        "inf,0,a",
        "-inf,0,a",
        "not-a-number,0,a",
        "0,,a",
    ],
)
def test_load_points_rejects_invalid_coordinates(
    tmp_path: Path,
    row: str,
) -> None:
    source: Path = tmp_path / "invalid-coordinate.csv"
    source.write_text(f"x,y,category\n{row}\n", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"^point coordinates must be numeric and finite$",
    ):
        load_points(source)
