"""Tests for the interactive Datashader notebook."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from gc import collect
from pathlib import Path
from typing import Protocol, cast
from weakref import ReferenceType, ref

import ipywidgets as widgets  # type: ignore[import-untyped]
import nbformat
import pandas as pd  # type: ignore[import-untyped]
import pytest
from nbclient import NotebookClient
from nbformat import NotebookNode
from PIL.Image import Image

from . import solution_00
from .solution_00 import (
    build_interactive_plot,
    dispose_interactive_plot,
    render_resolution,
)

POINTS: Path = Path(__file__).parents[1] / "exercise_01" / "points.csv"
NOTEBOOK: Path = Path(__file__).with_name("datashader_interactive.ipynb")
REPOSITORY: Path = Path(__file__).parents[2]
READ_CSV: Callable[[Path], pd.DataFrame] = cast(
    Callable[[Path], pd.DataFrame],
    pd.read_csv,  # pyright: ignore[reportUnknownMemberType]
)
READ_NOTEBOOK: Callable[..., NotebookNode] = cast(
    Callable[..., NotebookNode],
    nbformat.read,  # pyright: ignore[reportUnknownMemberType]
)


class _NotebookCell(Protocol):
    cell_type: str
    execution_count: int | None
    outputs: list[dict[str, object]]
    source: str


class _NotebookView(Protocol):
    nbformat: int
    metadata: Mapping[str, object]
    cells: list[_NotebookCell]


class _WidgetBox(Protocol):
    children: tuple[object, ...]


class _Closable(Protocol):
    def close(self) -> None: ...


class _Slider(Protocol):
    min: int
    max: int
    step: int
    value: int


def test_render_resolution_changes_image_dimensions() -> None:
    frame: pd.DataFrame = READ_CSV(POINTS)

    assert render_resolution(frame, 32).to_pil().size == (32, 32)
    assert render_resolution(frame, 64).to_pil().size == (64, 64)


def test_render_resolution_rejects_nonpositive_values() -> None:
    frame: pd.DataFrame = READ_CSV(POINTS)

    with pytest.raises(ValueError, match=r"^resolution must be positive$"):
        render_resolution(frame, 0)


def test_widget_has_bounded_control_and_updates_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame: pd.DataFrame = READ_CSV(POINTS)
    rendered_sizes: list[tuple[int, int]] = []

    def record_display(value: Image) -> None:
        rendered_sizes.append(value.size)

    monkeypatch.setattr(solution_00, "display", record_display)
    widget: widgets.VBox = build_interactive_plot(frame)
    children: tuple[object, ...] = cast(_WidgetBox, widget).children

    assert len(children) == 2
    assert isinstance(children[0], widgets.IntSlider)
    assert isinstance(children[1], widgets.Output)
    slider: _Slider = cast(_Slider, children[0])
    assert (slider.min, slider.max, slider.step, slider.value) == (32, 256, 32, 64)
    assert rendered_sizes == [(64, 64)]

    slider.value = 96
    assert rendered_sizes == [(64, 64), (96, 96)]


def test_dispose_interactive_plot_releases_frame_and_closes_widgets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame: pd.DataFrame = READ_CSV(POINTS)
    frame_reference: ReferenceType[pd.DataFrame] = ref(frame)
    rendered_sizes: list[tuple[int, int]] = []

    def record_display(value: Image) -> None:
        rendered_sizes.append(value.size)

    monkeypatch.setattr(solution_00, "display", record_display)
    widget: widgets.VBox = build_interactive_plot(frame)
    children: tuple[object, ...] = cast(_WidgetBox, widget).children
    slider: _Slider = cast(_Slider, children[0])
    slider_widget: _Closable = cast(_Closable, children[0])
    output_widget: _Closable = cast(_Closable, children[1])
    closed: list[str] = []
    slider_close: Callable[[], None] = slider_widget.close
    output_close: Callable[[], None] = output_widget.close
    container_close: Callable[[], None] = widget.close

    def close_slider() -> None:
        closed.append("slider")
        slider_close()

    def close_output() -> None:
        closed.append("output")
        output_close()

    def close_container() -> None:
        closed.append("container")
        container_close()

    monkeypatch.setattr(children[0], "close", close_slider)
    monkeypatch.setattr(children[1], "close", close_output)
    monkeypatch.setattr(widget, "close", close_container)
    del frame
    collect()
    assert frame_reference() is not None

    dispose_interactive_plot(widget)
    slider.value = 96
    collect()

    assert rendered_sizes == [(64, 64)]
    assert closed == ["slider", "output", "container"]
    assert frame_reference() is None


def test_notebook_is_clean_and_reproducible() -> None:
    notebook: NotebookNode = READ_NOTEBOOK(NOTEBOOK, as_version=4)
    notebook_view: _NotebookView = cast(_NotebookView, notebook)

    assert notebook_view.nbformat == 4
    assert notebook_view.metadata["kernelspec"] == {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    assert "widgets" not in notebook_view.metadata
    assert len(notebook_view.cells) == 3
    assert all(cell.cell_type == "code" for cell in notebook_view.cells)
    assert all(cell.execution_count is None for cell in notebook_view.cells)
    assert all(cell.outputs == [] for cell in notebook_view.cells)
    assert "def find_repository_root(start: Path) -> Path:" in (
        notebook_view.cells[0].source
    )
    assert "repository_root != current_directory" in notebook_view.cells[0].source
    assert "repository_root_text not in sys.path" in notebook_view.cells[0].source
    assert (
        "CH_15_scientific_python/exercise_01/points.csv"
        in notebook_view.cells[1].source
    )
    assert "points: Path = repository_root /" in notebook_view.cells[1].source
    assert "assert tuple(frame.shape) == (6, 3)" in notebook_view.cells[2].source
    assert "assert widget.children[0].value == 64" in notebook_view.cells[2].source


@pytest.mark.timeout(90)
@pytest.mark.parametrize(
    "working_directory",
    [REPOSITORY, NOTEBOOK.parent],
    ids=["repository-root", "notebook-directory"],
)
def test_notebook_executes_headlessly(working_directory: Path) -> None:
    notebook: NotebookNode = READ_NOTEBOOK(NOTEBOOK, as_version=4)
    client: NotebookClient = NotebookClient(
        notebook,
        timeout=60,
        kernel_name="python3",
    )

    executed: NotebookNode = client.execute(cwd=str(working_directory))
    executed_view: _NotebookView = cast(_NotebookView, executed)

    assert all(
        output.get("output_type") != "error"
        for cell in executed_view.cells
        for output in cell.outputs
    )
