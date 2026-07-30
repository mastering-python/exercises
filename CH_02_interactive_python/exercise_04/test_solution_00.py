"""Tests for the editable Hello widget."""

from __future__ import annotations

import gc
import subprocess
import sys
import weakref
from collections.abc import Callable, Mapping
from dataclasses import FrozenInstanceError
from typing import Protocol, cast

import IPython.display
import ipywidgets as widgets  # type: ignore[import-untyped]
import pytest
from traitlets import Bunch

import CH_02_interactive_python.exercise_04.solution_00 as solution_00
from CH_02_interactive_python.exercise_04.solution_00 import (
    HelloWidget,
    create_hello_widget,
)


class _ChangeNotifier(Protocol):
    def notify_change(self, change: Bunch, /) -> None: ...


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


def test_non_string_observer_value_falls_back_to_world() -> None:
    hello: HelloWidget = create_hello_widget("Ada")
    change: Bunch = Bunch(
        name="value",
        old="Ada",
        new=42,
        owner=hello.name_input,
        type="change",
    )
    notifier: _ChangeNotifier = cast(_ChangeNotifier, hello.name_input)

    notifier.notify_change(change)

    assert hello.greeting.value == "Hello, World!"


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


def test_close_preserves_external_observer_and_stops_greeting_updates() -> None:
    hello: HelloWidget = create_hello_widget("Ada")
    external_values: list[object] = []

    def observe_external(change: Mapping[str, object]) -> None:
        external_values.append(change["new"])

    hello.name_input.observe(observe_external, names="value")

    hello.close()
    hello.close()
    hello.name_input.value = "Grace"

    assert hello.greeting.value == "Hello, Ada!"
    assert external_values == ["Grace"]


def test_close_closes_each_owned_widget_exactly_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hello: HelloWidget = create_hello_widget()
    owned_widgets: tuple[object, ...] = (
        hello.name_input,
        hello.greeting,
        hello.container,
    )
    close_calls: dict[int, int] = {id(widget): 0 for widget in owned_widgets}

    def counting_close(
        widget_id: int,
        original_close: Callable[..., None],
    ) -> Callable[..., None]:
        def record_close(*args: object, **kwargs: object) -> None:
            close_calls[widget_id] += 1
            original_close(*args, **kwargs)

        return record_close

    comm_attribute: str = "comm"
    close_attribute: str = "close"
    for widget in owned_widgets:
        comm: object = getattr(widget, comm_attribute)
        original_close: Callable[..., None] = cast(
            Callable[..., None],
            getattr(comm, close_attribute),
        )
        monkeypatch.setattr(
            comm,
            close_attribute,
            counting_close(id(widget), original_close),
        )

    hello.close()
    hello.close()

    assert close_calls == {id(widget): 1 for widget in owned_widgets}
    assert all(getattr(widget, comm_attribute) is None for widget in owned_widgets)


def test_close_releases_internal_greeting_reference() -> None:
    hello: HelloWidget = create_hello_widget()
    retained_name_input: widgets.Text = hello.name_input
    greeting_reference: weakref.ReferenceType[widgets.Label] = weakref.ref(
        hello.greeting,
    )

    hello.close()
    del hello
    gc.collect()

    assert greeting_reference() is None
    assert retained_name_input.value == "World"


def test_close_retries_failed_widget_after_attempting_remaining_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hello: HelloWidget = create_hello_widget("Ada")
    external_values: list[object] = []

    def observe_external(change: Mapping[str, object]) -> None:
        external_values.append(change["new"])

    hello.name_input.observe(observe_external, names="value")
    unobserve_attribute: str = "unobserve"
    original_unobserve: Callable[..., None] = cast(
        Callable[..., None],
        getattr(hello.name_input, unobserve_attribute),
    )
    unobserve_calls: int = 0

    def record_unobserve(*args: object, **kwargs: object) -> None:
        nonlocal unobserve_calls
        unobserve_calls += 1
        original_unobserve(*args, **kwargs)

    monkeypatch.setattr(
        hello.name_input,
        unobserve_attribute,
        record_unobserve,
    )
    close_attribute: str = "close"
    original_name_close: Callable[[], None] = cast(
        Callable[[], None],
        getattr(hello.name_input, close_attribute),
    )
    name_close_calls: int = 0
    close_error: RuntimeError = RuntimeError("name close failed")

    def fail_name_close_once() -> None:
        nonlocal name_close_calls
        name_close_calls += 1
        if name_close_calls == 1:
            raise close_error
        original_name_close()

    monkeypatch.setattr(
        hello.name_input,
        close_attribute,
        fail_name_close_once,
    )

    with pytest.raises(RuntimeError, match="name close failed") as error_info:
        hello.close()

    assert error_info.value is close_error
    comm_attribute: str = "comm"
    assert getattr(hello.name_input, comm_attribute) is not None
    assert getattr(hello.greeting, comm_attribute) is None
    assert getattr(hello.container, comm_attribute) is None

    hello.close()
    hello.name_input.value = "Grace"

    assert name_close_calls == 2
    assert unobserve_calls == 1
    assert getattr(hello.name_input, comm_attribute) is None
    assert hello.greeting.value == "Hello, Ada!"
    assert external_values == ["Grace"]


def test_close_retries_transient_unobserve_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    hello: HelloWidget = create_hello_widget("Ada")
    external_values: list[object] = []

    def observe_external(change: Mapping[str, object]) -> None:
        external_values.append(change["new"])

    hello.name_input.observe(observe_external, names="value")
    unobserve_attribute: str = "unobserve"
    original_unobserve: Callable[..., None] = cast(
        Callable[..., None],
        getattr(hello.name_input, unobserve_attribute),
    )
    unobserve_calls: int = 0
    unobserve_error: RuntimeError = RuntimeError("unobserve failed")

    def fail_unobserve_once(*args: object, **kwargs: object) -> None:
        nonlocal unobserve_calls
        unobserve_calls += 1
        if unobserve_calls == 1:
            raise unobserve_error
        original_unobserve(*args, **kwargs)

    monkeypatch.setattr(
        hello.name_input,
        unobserve_attribute,
        fail_unobserve_once,
    )

    with pytest.raises(RuntimeError, match="unobserve failed") as error_info:
        hello.close()

    assert error_info.value is unobserve_error
    comm_attribute: str = "comm"
    assert getattr(hello.name_input, comm_attribute) is None
    assert getattr(hello.greeting, comm_attribute) is None
    assert getattr(hello.container, comm_attribute) is None
    hello.name_input.value = "Grace"
    assert hello.greeting.value == "Hello, Grace!"

    hello.close()
    hello.close()
    hello.name_input.value = "Katherine"

    assert unobserve_calls == 2
    assert hello.greeting.value == "Hello, Grace!"
    assert external_values == ["Grace", "Katherine"]


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
