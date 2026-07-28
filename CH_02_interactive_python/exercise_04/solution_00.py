"""Create an editable greeting widget for notebook use."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import cast

import ipywidgets as widgets  # type: ignore[import-untyped]


@dataclass(frozen=True)
class HelloWidget:
    """Widgets that make up an editable greeting."""

    name_input: widgets.Text
    greeting: widgets.Label
    container: widgets.VBox


def _greeting_text(name: str) -> str:
    displayed_name: str = name.strip() or "World"
    return f"Hello, {displayed_name}!"


def create_hello_widget(initial_name: str = "World") -> HelloWidget:
    """Create independent editable greeting state."""
    name_input: widgets.Text = widgets.Text(
        value=initial_name,
        description="Name",
    )
    greeting: widgets.Label = widgets.Label(value=_greeting_text(initial_name))

    def update_greeting(change: Mapping[str, object]) -> None:
        raw_name: object = change["new"]
        name: str = raw_name.strip() if isinstance(raw_name, str) else ""
        greeting.value = _greeting_text(name)

    name_input.observe(update_greeting, names="value")
    container: widgets.VBox = widgets.VBox(children=(name_input, greeting))
    return HelloWidget(
        name_input=name_input,
        greeting=greeting,
        container=container,
    )


def main() -> None:
    """Display the editable greeting in an IPython frontend."""
    from IPython.display import display  # pyright: ignore[reportUnknownVariableType]

    hello: HelloWidget = create_hello_widget()
    display_widget: Callable[[object], object] = cast(
        Callable[[object], object],
        display,
    )
    display_widget(hello.container)


if __name__ == "__main__":
    main()
