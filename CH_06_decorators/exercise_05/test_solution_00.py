"""Tests for the recalculable cached-property descriptor."""

from collections.abc import Callable
from typing import NoReturn

import pytest

from .solution_00 import CachedProperty


def test_instances_cache_independently_and_deletion_recalculates() -> None:
    calls: list[str] = []

    class Example:
        def __init__(self, value: str) -> None:
            self.value: str = value

        @CachedProperty
        def rendered(self) -> object:
            calls.append(self.value)
            return object()

    first: Example = Example("first")
    second: Example = Example("second")

    first_result: object = first.rendered
    second_result: object = second.rendered

    assert first.rendered is first_result
    assert second.rendered is second_result
    assert calls == ["first", "second"]
    assert vars(first)["rendered"] is first_result
    assert vars(second)["rendered"] is second_result

    del first.rendered

    replacement: object = first.rendered
    assert replacement is not first_result
    assert second.rendered is second_result
    assert calls == ["first", "second", "first"]


def test_deletion_before_first_access_names_the_property() -> None:
    class Example:
        @CachedProperty
        def value(self) -> int:
            return 1

    example: Example = Example()

    with pytest.raises(AttributeError, match=r"^value$"):
        del example.value


def test_class_access_returns_the_descriptor() -> None:
    class Example:
        @CachedProperty
        def value(self) -> int:
            return 1

    descriptor: CachedProperty[Example, int] = Example.value

    assert isinstance(descriptor, CachedProperty)
    assert descriptor is vars(Example)["value"]


def test_one_descriptor_cannot_bind_to_two_names() -> None:
    class Example:
        def value(self) -> int:
            return 1

    descriptor: CachedProperty[Example, int] = CachedProperty(Example.value)
    descriptor.__set_name__(Example, "first")

    with pytest.raises(
        TypeError,
        match=r"^Cannot assign the same CachedProperty to two different names "
        r"\('first' and 'second'\)\.$",
    ):
        descriptor.__set_name__(Example, "second")


def test_unbound_descriptor_access_raises_type_error() -> None:
    class Example:
        def value(self) -> int:
            return 1

    descriptor: CachedProperty[Example, int] = CachedProperty(Example.value)
    example: Example = Example()

    with pytest.raises(
        TypeError,
        match=r"^CachedProperty has not been assigned to a class attribute$",
    ):
        descriptor.__get__(example, Example)


def test_unbound_descriptor_class_access_raises_type_error() -> None:
    class Example:
        def value(self) -> int:
            return 1

    descriptor: CachedProperty[Example, int] = CachedProperty(Example.value)

    with pytest.raises(
        TypeError,
        match=r"^CachedProperty has not been assigned to a class attribute$",
    ):
        descriptor.__get__(None, Example)


def test_slots_only_instance_requires_instance_dict() -> None:
    class Slotted:
        __slots__: tuple[()] = ()

        @CachedProperty
        def value(self) -> int:
            return 1

    with pytest.raises(
        TypeError,
        match=r"^CachedProperty 'value' requires instances with a __dict__$",
    ):
        assert Slotted().value == 1


def test_none_is_cached_and_function_is_called_once() -> None:
    calls: list[int] = []

    class Example:
        @CachedProperty
        def value(self) -> None:
            calls.append(1)
            return None

    example: Example = Example()

    assert example.value is None
    assert example.value is None
    assert calls == [1]
    assert "value" in vars(example)


def test_function_metadata_is_preserved() -> None:
    def original(self: object) -> int:
        """Return the answer."""
        return 42

    original.category = "answer"  # type: ignore[attr-defined]
    descriptor: CachedProperty[object, int] = CachedProperty(original)

    assert descriptor.__name__ == "original"
    assert descriptor.__doc__ == "Return the answer."
    assert descriptor.__module__ == original.__module__
    assert descriptor.__annotations__ == original.__annotations__
    assert descriptor.__wrapped__ is original
    assert descriptor.category == "answer"  # type: ignore[attr-defined]


def test_exception_is_not_cached() -> None:
    calls: list[int] = []

    class Example:
        @CachedProperty
        def value(self) -> NoReturn:
            calls.append(1)
            raise RuntimeError("boom")

    example: Example = Example()

    def read_value() -> object:
        return example.value

    for _ in range(2):
        with pytest.raises(RuntimeError, match=r"^boom$"):
            read_value()

    assert calls == [1, 1]
    assert "value" not in vars(example)


def test_public_constructor_accepts_a_typed_callable() -> None:
    class Example:
        def value(self) -> str:
            return "value"

    function: Callable[[Example], str] = Example.value
    descriptor: CachedProperty[Example, str] = CachedProperty(function)

    assert descriptor.func is function
