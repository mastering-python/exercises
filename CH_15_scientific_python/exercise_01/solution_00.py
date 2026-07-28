"""Create deterministic Datashader plots from a local point fixture."""

from __future__ import annotations

from collections.abc import Callable
from math import isfinite
from numbers import Real
from pathlib import Path
from typing import cast

import datashader as ds  # type: ignore[import-untyped]
import datashader.transfer_functions as tf  # type: ignore[import-untyped]
import pandas as pd  # type: ignore[import-untyped]
import xarray as xr

__all__: list[str] = [
    "aggregate_points",
    "load_points",
    "render_points",
    "save_plot",
]

X_RANGE: tuple[float, float] = (-1.1, 1.1)
Y_RANGE: tuple[float, float] = (-1.1, 1.1)
COLOR_MAP: tuple[str, ...] = ("#0b132b", "#3a86ff", "#ffbe0b")
READ_CSV: Callable[[Path], pd.DataFrame] = cast(
    Callable[[Path], pd.DataFrame],
    pd.read_csv,  # pyright: ignore[reportUnknownMemberType]
)


def _coordinates_are_valid(frame: pd.DataFrame) -> bool:
    for column_name in ("x", "y"):
        values: list[object] = cast(
            list[object],
            frame[column_name].tolist(),  # pyright: ignore[reportUnknownMemberType]
        )
        for value in values:
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not isfinite(float(value))
            ):
                return False
    return True


def load_points(path: Path) -> pd.DataFrame:
    """Load the exact point-table schema from ``path``."""

    frame: pd.DataFrame = READ_CSV(path)
    if list(frame.columns) != ["x", "y", "category"]:
        raise ValueError("point data must contain exactly x, y, category columns")
    if frame.empty:
        raise ValueError("point data must not be empty")
    if not _coordinates_are_valid(frame):
        raise ValueError("point coordinates must be numeric and finite")
    return frame


def aggregate_points(
    frame: pd.DataFrame,
    *,
    width: int = 256,
    height: int = 256,
) -> xr.DataArray:
    """Count points on a fixed-range raster."""

    if width < 1 or height < 1:
        raise ValueError("plot dimensions must be positive")
    canvas: ds.Canvas = ds.Canvas(
        plot_width=width,
        plot_height=height,
        x_range=X_RANGE,
        y_range=Y_RANGE,
    )
    aggregate: xr.DataArray = cast(
        xr.DataArray,
        canvas.points(  # pyright: ignore[reportUnknownMemberType]
            frame,
            "x",
            "y",
            agg=ds.count(),
        ),
    )
    return aggregate


def render_points(
    frame: pd.DataFrame,
    *,
    width: int = 256,
    height: int = 256,
) -> tf.Image:
    """Render a point count with a fixed linear color map."""

    aggregate: xr.DataArray = aggregate_points(
        frame,
        width=width,
        height=height,
    )
    image: tf.Image = cast(
        tf.Image,
        tf.shade(  # pyright: ignore[reportUnknownMemberType]
            aggregate,
            cmap=list(COLOR_MAP),
            how="linear",
        ),
    )
    return image


def save_plot(
    source: Path,
    destination: Path,
    *,
    width: int = 256,
    height: int = 256,
) -> Path:
    """Render ``source`` and save a PNG to ``destination``."""

    image: tf.Image = render_points(
        load_points(source),
        width=width,
        height=height,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.to_pil().save(destination, format="PNG")
    return destination


def main() -> None:
    """Write a deterministic demonstration plot beside this module."""

    source: Path = Path(__file__).with_name("points.csv")
    destination: Path = Path(__file__).with_name("datashader_plot.png")
    saved: Path = save_plot(source, destination)
    print(saved)


if __name__ == "__main__":
    main()
