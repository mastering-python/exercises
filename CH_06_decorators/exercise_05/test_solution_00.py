"""Tests for the recalculable cached-property descriptor."""

import sys
from collections.abc import Callable
from functools import partial
from typing import NoReturn, cast

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

    descriptor: CachedProperty[object, int] = CachedProperty(original)

    assert descriptor.__name__ == "original"
    assert descriptor.__qualname__ == original.__qualname__
    assert descriptor.__doc__ == "Return the answer."
    assert descriptor.__module__ == original.__module__
    assert descriptor.__annotations__ == original.__annotations__
    assert descriptor.__wrapped__ is original


def test_valid_type_parameters_are_preserved_when_present() -> None:
    def original(self: object) -> int:
        return 42

    type_parameters: tuple[object, ...] = (object(),)
    original.__type_params__ = type_parameters  # type: ignore[attr-defined]

    descriptor: CachedProperty[object, int] = CachedProperty(original)

    assert descriptor.__type_params__ == type_parameters


def test_native_type_parameters_are_preserved_on_supported_python() -> None:
    if sys.version_info < (3, 12):
        pytest.skip("generic function syntax requires Python 3.12 or newer")

    namespace: dict[str, object] = {}
    source: str = "def generic[T](self: object) -> object:\n    return self\n"
    exec(source, namespace)
    function: Callable[[object], object] = cast(
        Callable[[object], object],
        namespace["generic"],
    )

    descriptor: CachedProperty[object, object] = CachedProperty(function)
    type_parameters: object = object.__getattribute__(function, "__type_params__")

    assert isinstance(type_parameters, tuple)
    assert descriptor.__type_params__ == type_parameters


def test_malformed_type_parameters_are_ignored() -> None:
    class MalformedTypeParameters:
        def __call__(self, instance: object) -> int:
            return 42

        def __getattribute__(self, attribute: str) -> object:
            if attribute == "__type_params__":
                return ["not", "a", "tuple"]
            return object.__getattribute__(self, attribute)

    function: Callable[[object], int] = MalformedTypeParameters()
    descriptor: CachedProperty[object, int] = CachedProperty(function)

    assert descriptor.__type_params__ == ()


def test_malformed_standard_metadata_is_ignored() -> None:
    class MalformedMetadata:
        def __call__(self, instance: object) -> int:
            return 42

        def __getattribute__(self, attribute: str) -> object:
            malformed: dict[str, object] = {
                "__module__": 1,
                "__name__": 2,
                "__qualname__": 3,
                "__doc__": 4,
                "__annotations__": (),
                "__type_params__": [],
            }
            if attribute in malformed:
                return malformed[attribute]
            return object.__getattribute__(self, attribute)

    function: Callable[[object], int] = MalformedMetadata()
    descriptor: CachedProperty[object, int] = CachedProperty(function)
    copied: dict[str, object] = vars(descriptor)

    assert isinstance(copied["__module__"], str)
    assert isinstance(copied["__name__"], str)
    assert isinstance(copied["__qualname__"], str)
    assert copied["__doc__"] is None
    assert copied["__annotations__"] == {}
    assert copied["__type_params__"] == ()
    assert descriptor.__annotations__ == {}
    assert "function" not in descriptor.__annotations__
    assert descriptor.__wrapped__ is function


def test_hostile_annotations_dict_is_not_iterated() -> None:
    class ExplodingDict(dict[str, object]):
        def __iter__(self) -> NoReturn:
            raise RuntimeError("do not iterate")

    def original(self: object) -> int:
        return 42

    original.__annotations__ = ExplodingDict({"return": int})

    descriptor: CachedProperty[object, int] = CachedProperty(original)

    assert descriptor.__annotations__ == {}


def test_partial_is_a_supported_callable() -> None:
    class Example:
        pass

    def render(prefix: str, instance: Example) -> str:
        return f"{prefix}:{type(instance).__name__}"

    function: Callable[[Example], str] = partial(render, "partial")
    descriptor: CachedProperty[Example, str] = CachedProperty(function)
    descriptor.__set_name__(Example, "rendered")
    example: Example = Example()

    assert descriptor.__get__(example, Example) == "partial:Example"
    assert isinstance(descriptor.__module__, str)
    assert isinstance(descriptor.__name__, str)
    assert isinstance(descriptor.__qualname__, str)
    assert descriptor.__doc__ is None or isinstance(descriptor.__doc__, str)
    assert descriptor.__annotations__ == {}
    assert descriptor.__type_params__ == ()


def test_slotted_callable_is_supported() -> None:
    class Example:
        pass

    class Render:
        __slots__: tuple[()] = ()

        def __call__(self, instance: Example) -> str:
            return type(instance).__name__

    function: Callable[[Example], str] = Render()
    descriptor: CachedProperty[Example, str] = CachedProperty(function)
    descriptor.__set_name__(Example, "rendered")
    example: Example = Example()

    assert descriptor.__get__(example, Example) == "Example"
    assert isinstance(descriptor.__module__, str)
    assert isinstance(descriptor.__name__, str)
    assert isinstance(descriptor.__qualname__, str)
    assert descriptor.__doc__ is None or isinstance(descriptor.__doc__, str)
    assert descriptor.__annotations__ == {}
    assert descriptor.__type_params__ == ()


def test_hostile_callable_dict_is_not_iterated() -> None:
    class HostileDict(dict[str, object]):
        def __iter__(self) -> NoReturn:
            raise RuntimeError("do not iterate")

        def items(self) -> NoReturn:
            raise RuntimeError("do not inspect items")

    class Example:
        pass

    class Render:
        def __call__(self, instance: Example) -> str:
            return type(instance).__name__

        def __getattribute__(self, attribute: str) -> object:
            if attribute == "__dict__":
                return HostileDict({"category": "unsafe"})
            return object.__getattribute__(self, attribute)

    function: Callable[[Example], str] = Render()
    descriptor: CachedProperty[Example, str] = CachedProperty(function)
    descriptor.__set_name__(Example, "rendered")

    assert descriptor.__get__(Example(), Example) == "Example"
    assert "category" not in vars(descriptor)


def test_callable_attributes_cannot_shadow_descriptor_internals() -> None:
    class Example:
        pass

    def original(instance: Example) -> str:
        return type(instance).__name__

    attributes: dict[str, object] = vars(original)
    attributes["_bound_name"] = "shadowed"
    attributes["_instance_storage"] = "shadowed"
    attributes["function"] = "shadowed"
    attributes["name"] = "shadowed"
    attributes["category"] = "preserved"

    descriptor: CachedProperty[Example, str] = CachedProperty(original)

    assert descriptor.function is original
    assert descriptor.name is None
    assert "_bound_name" not in vars(descriptor)
    assert "_instance_storage" not in vars(descriptor)
    assert descriptor.category == "preserved"  # type: ignore[attr-defined]

    descriptor.__set_name__(Example, "rendered")

    assert descriptor.name == "rendered"
    assert descriptor.__get__(Example(), Example) == "Example"


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

    assert descriptor.function is function
    assert descriptor.name is None
