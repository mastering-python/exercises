"""Build an interactive resolution control for the Datashader plot."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast
from weakref import WeakKeyDictionary

import datashader.transfer_functions as tf  # type: ignore[import-untyped]
import ipywidgets as widgets  # type: ignore[import-untyped]
import pandas as pd  # type: ignore[import-untyped]
from IPython.display import (
    display as untyped_display,  # pyright: ignore[reportUnknownVariableType]
)

from CH_15_scientific_python.exercise_01.solution_00 import render_points

__all__: list[str] = [
    "build_interactive_plot",
    "dispose_interactive_plot",
    "render_resolution",
]

display: Callable[[object], object] = cast(
    Callable[[object], object],
    untyped_display,
)
Observer = Callable[[dict[str, object]], None]


@dataclass(slots=True)
class _InteractivePlotState:
    slider: widgets.IntSlider
    output: widgets.Output
    observer: Observer | None

    def dispose(self, container: widgets.VBox) -> None:
        first_error: Exception | None = None
        observer: Observer | None = self.observer
        self.observer = None
        if observer is not None:
            try:
                self.slider.unobserve(observer, names="value")
            except Exception as error:
                first_error = error

        closers: tuple[Callable[[], None], ...] = (
            self.slider.close,
            self.output.close,
            container.close,
        )
        for close in closers:
            try:
                close()
            except Exception as error:
                if first_error is None:
                    first_error = error

        if first_error is not None:
            raise first_error


_INTERACTIVE_PLOTS: WeakKeyDictionary[
    widgets.VBox,
    _InteractivePlotState,
] = WeakKeyDictionary()


def render_resolution(frame: pd.DataFrame, resolution: int) -> tf.Image:
    """Render ``frame`` as a square image at ``resolution`` pixels."""

    if resolution < 1:
        raise ValueError("resolution must be positive")
    return render_points(
        frame,
        width=resolution,
        height=resolution,
    )


def build_interactive_plot(frame: pd.DataFrame) -> widgets.VBox:
    """Return a bounded resolution slider and its rendered output."""

    slider: widgets.IntSlider = widgets.IntSlider(
        value=64,
        min=32,
        max=256,
        step=32,
        description="Resolution",
    )
    output: widgets.Output = widgets.Output()
    clear_output: Callable[..., None] = cast(
        Callable[..., None],
        output.clear_output,  # pyright: ignore[reportUnknownMemberType]
    )

    def update(change: dict[str, object]) -> None:
        resolution_value: object = change["new"]
        if not isinstance(resolution_value, int):
            raise TypeError("resolution widget returned a non-integer")
        with output:
            clear_output(wait=True)
            display(render_resolution(frame, resolution_value).to_pil())

    slider.observe(update, names="value")
    with output:
        display(render_resolution(frame, 64).to_pil())
    container: widgets.VBox = widgets.VBox((slider, output))
    _INTERACTIVE_PLOTS[container] = _InteractivePlotState(
        slider=slider,
        output=output,
        observer=update,
    )
    return container


def dispose_interactive_plot(container: widgets.VBox) -> None:
    """Unregister observers, release captured data, close owned widgets."""
    state: _InteractivePlotState | None = _INTERACTIVE_PLOTS.pop(
        container,
        None,
    )
    if state is not None:
        state.dispose(container)
