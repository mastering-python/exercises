"""Create an editable greeting widget for notebook use."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import cast

import ipywidgets as widgets  # type: ignore[import-untyped]


@dataclass(frozen=True)
class HelloWidget:
    """Widgets that make up an editable greeting."""

    name_input: widgets.Text
    greeting: widgets.Label
    container: widgets.VBox
    _observer: Callable[[Mapping[str, object]], None] | None = field(
        default=None,
        init=False,
        repr=False,
        compare=False,
    )
    _closed: bool = field(
        default=False,
        init=False,
        repr=False,
        compare=False,
    )

    def close(self) -> None:
        """Unregister internal state and close every owned widget once."""
        if self._closed:
            return

        first_error: Exception | None = None
        if self._observer is not None:
            try:
                self.name_input.unobserve(self._observer, names="value")
            except Exception as error:
                first_error = error
            else:
                object.__setattr__(self, "_observer", None)

        for widget in (self.name_input, self.greeting, self.container):
            try:
                widget.close()
            except Exception as error:
                if first_error is None:
                    first_error = error

        if first_error is not None:
            raise first_error
        object.__setattr__(self, "_closed", True)


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
    hello: HelloWidget = HelloWidget(
        name_input=name_input,
        greeting=greeting,
        container=container,
    )
    object.__setattr__(hello, "_observer", update_greeting)
    return hello


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
