"""Tests for configurable multi-argument single dispatch."""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable
from typing import Any, cast

import pytest

from .solution_00 import fancysingledispatch


def test_explicit_multi_argument_dispatch_supports_positional_and_keywords() -> None:
    @fancysingledispatch(dispatch_on=("left", "right"))
    def combine(left: object, right: object, separator: str = ":") -> str:
        return f"base{separator}{left}{separator}{right}"

    @combine.register
    def _combine_strings(left: str, right: str, separator: str = ":") -> str:
        return separator.join((left, right))

    assert callable(_combine_strings)
    assert combine("alpha", "beta") == "alpha:beta"
    assert combine(left="alpha", right="beta", separator="/") == "alpha/beta"
    assert combine("alpha", 2) == "base:alpha:2"


def test_default_configuration_dispatches_on_every_parameter() -> None:
    @fancysingledispatch()
    def describe(value: object, enabled: object) -> str:
        return "base"

    @describe.register
    def _describe_integer(value: int, enabled: bool) -> str:
        return f"{value}:{enabled}"

    assert callable(_describe_integer)
    assert describe(3, True) == "3:True"
    assert describe(3, 1) == "base"


def test_legacy_positional_exclusions_are_supported() -> None:
    @fancysingledispatch("context")
    def render(value: object, context: object) -> str:
        return "base"

    @render.register
    def _render_integer(value: int, context: str) -> str:
        return f"{context}:{value}"

    assert callable(_render_integer)
    assert render(4, "decimal") == "decimal:4"
    assert render(4, object()).endswith(":4")


def test_legacy_true_keyword_exclusions_are_supported() -> None:
    @fancysingledispatch(context=True)
    def render(value: object, context: object) -> str:
        return "base"

    @render.register
    def _render_integer(value: int, context: object) -> str:
        return f"{type(context).__name__}:{value}"

    assert callable(_render_integer)
    assert render(4, "text") == "str:4"
    assert render(4, 5) == "int:4"


def test_false_legacy_keyword_is_rejected() -> None:
    with pytest.raises(
        TypeError,
        match=r"^ignored keyword 'context' must be True$",
    ):
        fancysingledispatch(context=False)


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda: fancysingledispatch("context", dispatch_on=("value",)),
            "dispatch_on cannot be combined with ignored parameter names",
        ),
        (
            lambda: fancysingledispatch(
                dispatch_on=("value",),
                context=True,
            ),
            "dispatch_on cannot be combined with ignored parameter names",
        ),
        (
            lambda: fancysingledispatch(dispatch_on=()),
            "dispatch_on must contain at least one parameter name",
        ),
        (
            lambda: fancysingledispatch("context", "context"),
            "duplicate ignored parameter name: 'context'",
        ),
        (
            lambda: fancysingledispatch("context", context=True),
            "duplicate ignored parameter name: 'context'",
        ),
        (
            lambda: fancysingledispatch(dispatch_on=("value", "value")),
            "duplicate dispatch parameter name: 'value'",
        ),
    ],
)
def test_invalid_factory_configurations_are_rejected(
    factory: Callable[[], object],
    message: str,
) -> None:
    with pytest.raises(TypeError, match=f"^{message}$"):
        factory()


def test_unknown_ignored_name_is_rejected_when_base_is_decorated() -> None:
    decorator = fancysingledispatch("missing")

    def base(value: object) -> str:
        return str(value)

    with pytest.raises(
        TypeError,
        match=r"^unknown ignored parameter name: 'missing'$",
    ):
        decorator(base)


def test_unknown_selected_name_is_rejected_when_base_is_decorated() -> None:
    decorator = fancysingledispatch(dispatch_on=("missing",))

    def base(value: object) -> str:
        return str(value)

    with pytest.raises(
        TypeError,
        match=r"^unknown dispatch parameter name: 'missing'$",
    ):
        decorator(base)


def test_defaults_are_applied_before_building_dispatch_key() -> None:
    @fancysingledispatch(dispatch_on=("count",))
    def repeat(text: str, count: object = 2) -> str:
        return "base"

    @repeat.register
    def _repeat_integer(text: str, count: int = 2) -> str:
        return text * count

    assert callable(_repeat_integer)
    assert repeat("go") == "gogo"
    assert repeat("go", count=3) == "gogogo"


def test_unregistered_types_call_base_and_subclasses_do_not_match() -> None:
    class Number(int):
        pass

    @fancysingledispatch(dispatch_on=("value",))
    def identify(value: object) -> str:
        return "base"

    @identify.register
    def _identify_integer(value: int) -> str:
        return "int"

    assert callable(_identify_integer)
    assert identify(1) == "int"
    assert identify(Number(1)) == "base"


def test_register_returns_function_and_duplicate_key_replaces_implementation() -> None:
    @fancysingledispatch(dispatch_on=("value",))
    def identify(value: object) -> str:
        return "base"

    def first(value: int) -> str:
        return "first"

    def second(value: int) -> str:
        return "second"

    assert identify.register(first) is first
    assert identify(1) == "first"
    assert identify.register(second) is second
    assert identify(1) == "second"


@pytest.mark.parametrize(
    ("annotation", "description"),
    [
        (None, "missing"),
        (Any, "typing.Any"),
        (int | str, "int | str"),
        (list[int], "list[int]"),
        (42, "42"),
    ],
)
def test_selected_parameter_requires_concrete_class_annotation(
    annotation: object | None,
    description: str,
) -> None:
    @fancysingledispatch(dispatch_on=("value",))
    def identify(value: object) -> str:
        return "base"

    def implementation(value: object) -> str:
        return str(value)

    if annotation is None:
        del implementation.__annotations__["value"]
    else:
        implementation.__annotations__["value"] = annotation

    with pytest.raises(
        TypeError,
        match=(
            r"^dispatch parameter 'value' must have a resolvable concrete "
            rf"class annotation; got {re.escape(description)}$"
        ),
    ):
        identify.register(implementation)


def test_unresolvable_forward_reference_is_rejected() -> None:
    @fancysingledispatch(dispatch_on=("value",))
    def identify(value: object) -> str:
        return "base"

    def implementation(value: object) -> str:
        return str(value)

    implementation.__annotations__["value"] = "MissingClass"

    with pytest.raises(
        TypeError,
        match=(
            r"^dispatch parameter annotations could not be resolved: "
            r"name 'MissingClass' is not defined$"
        ),
    ):
        identify.register(implementation)


def test_registration_requires_same_parameter_names_and_kinds() -> None:
    @fancysingledispatch(dispatch_on=("value",))
    def identify(value: object, /, label: str = "") -> str:
        return "base"

    def wrong_name(item: int, /, label: str = "") -> str:
        return f"{label}{item}"

    def wrong_kind(value: int, label: str = "") -> str:
        return f"{label}{value}"

    with pytest.raises(
        TypeError,
        match=r"^registered function parameters must match base names and kinds$",
    ):
        identify.register(cast(Callable[[object, str], str], wrong_name))

    with pytest.raises(
        TypeError,
        match=r"^registered function parameters must match base names and kinds$",
    ):
        identify.register(cast(Callable[[object, str], str], wrong_kind))


def test_metadata_wrapping_and_signature_are_preserved() -> None:
    def original(value: object, label: str = "value") -> str:
        """Describe a value."""
        return f"{label}:{value}"

    vars(original)["category"] = "formatter"
    original_signature: inspect.Signature = inspect.signature(original)
    decorated = fancysingledispatch(dispatch_on=("value",))(original)

    assert decorated.__name__ == "original"
    assert decorated.__doc__ == "Describe a value."
    assert vars(decorated)["category"] == "formatter"
    assert decorated.__wrapped__ is original
    assert inspect.signature(decorated) == original_signature


def test_argument_binding_errors_propagate() -> None:
    @fancysingledispatch(dispatch_on=("value",))
    def identify(value: object) -> str:
        return str(value)

    unchecked_identify = cast(Callable[..., str], identify)

    with pytest.raises(TypeError, match="missing a required argument: 'value'"):
        unchecked_identify()

    with pytest.raises(TypeError, match="too many positional arguments"):
        unchecked_identify(1, 2)
