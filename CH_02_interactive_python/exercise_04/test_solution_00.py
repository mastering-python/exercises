"""Tests for the editable Hello widget."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import FrozenInstanceError
from typing import cast

import IPython.display
import ipywidgets as widgets  # type: ignore[import-untyped]
import pytest

import CH_02_interactive_python.exercise_04.solution_00 as solution_00
from CH_02_interactive_python.exercise_04.solution_00 import (
    HelloWidget,
    create_hello_widget,
)


def test_initial_name_sets_text_and_greeting() -> None:
    hello: HelloWidget = create_hello_widget("Ada")

    assert hello.name_input.value == "Ada"
    assert hello.name_input.description == "Name"
    assert hello.greeting.value == "Hello, Ada!"


def test_editing_name_updates_existing_greeting_synchronously() -> None:
    hello: HelloWidget = create_hello_widget("Ada")

    hello.name_input.value = "Grace"

    assert hello.greeting.value == "Hello, Grace!"


@pytest.mark.parametrize("name", ["", " ", "\t\n"])
def test_empty_or_whitespace_name_falls_back_to_world(name: str) -> None:
    hello: HelloWidget = create_hello_widget("Ada")

    hello.name_input.value = name

    assert hello.greeting.value == "Hello, World!"


def test_nonempty_name_is_trimmed_in_greeting() -> None:
    hello: HelloWidget = create_hello_widget("  Ada Lovelace  ")

    assert hello.name_input.value == "  Ada Lovelace  "
    assert hello.greeting.value == "Hello, Ada Lovelace!"

    hello.name_input.value = "  Grace Hopper\t"

    assert hello.greeting.value == "Hello, Grace Hopper!"


def test_instances_have_independent_widget_state() -> None:
    ada: HelloWidget = create_hello_widget("Ada")
    grace: HelloWidget = create_hello_widget("Grace")

    ada.name_input.value = "Charles"

    assert ada.greeting.value == "Hello, Charles!"
    assert grace.name_input.value == "Grace"
    assert grace.greeting.value == "Hello, Grace!"
    assert ada.name_input is not grace.name_input
    assert ada.greeting is not grace.greeting
    assert ada.container is not grace.container


def test_container_has_exact_widget_types_and_order() -> None:
    hello: HelloWidget = create_hello_widget()
    children_attribute: str = "children"
    children: tuple[object, ...] = cast(
        tuple[object, ...],
        getattr(hello.container, children_attribute),
    )

    assert type(hello.name_input) is widgets.Text
    assert type(hello.greeting) is widgets.Label
    assert type(hello.container) is widgets.VBox
    assert children == (hello.name_input, hello.greeting)


def test_bundle_is_frozen() -> None:
    hello: HelloWidget = create_hello_widget()
    field_name: str = "greeting"

    with pytest.raises(FrozenInstanceError):
        setattr(hello, field_name, widgets.Label(value="replacement"))


def test_main_displays_only_the_container(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    displayed: list[object] = []

    def record_display(value: object) -> None:
        displayed.append(value)

    monkeypatch.setattr(IPython.display, "display", record_display)

    solution_00.main()

    assert len(displayed) == 1
    container: object = displayed[0]
    assert type(container) is widgets.VBox


def test_import_is_headless_and_has_no_output() -> None:
    script: str = """
import IPython.display
import webbrowser

def fail(*args: object, **kwargs: object) -> None:
    raise AssertionError("import attempted an interactive side effect")

IPython.display.display = fail
webbrowser.open = fail
import CH_02_interactive_python.exercise_04.solution_00
"""
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""
