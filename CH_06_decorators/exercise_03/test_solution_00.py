from dataclasses import dataclass
from inspect import signature
from typing import NoReturn

import pytest

from .solution_00 import cache, memoize


def setup_function() -> None:
    cache.clear()


def test_equivalent_list_and_dict_keyword_arguments_share_cache_entry() -> None:
    calls: list[int] = []

    @memoize
    def render(values: object, *, options: object) -> object:
        calls.append(1)
        return object()

    first: object = render([1, 2], options={"enabled": True})
    second: object = render([1, 2], options={"enabled": True})

    assert second is first
    assert calls == [1]
    assert len(cache) == 1


def test_list_and_tuple_arguments_have_separate_entries() -> None:
    calls: list[int] = []

    @memoize
    def identify(value: object) -> str:
        calls.append(1)
        return type(value).__name__

    assert identify([1, 2]) == "list"
    assert identify((1, 2)) == "tuple"
    assert calls == [1, 1]
    assert len(cache) == 2


def test_bool_and_int_arguments_have_separate_entries() -> None:
    calls: list[int] = []

    @memoize
    def identify(value: object) -> type[object]:
        calls.append(1)
        return type(value)

    assert identify(True) is bool
    assert identify(1) is int
    assert calls == [1, 1]
    assert len(cache) == 2


def test_dictionary_keys_are_frozen_with_runtime_type_tags() -> None:
    calls: list[int] = []

    @memoize
    def identify_key(mapping: dict[object, str]) -> str:
        calls.append(1)
        key: object = next(iter(mapping))
        return type(key).__name__

    assert identify_key({True: "value"}) == "bool"
    assert identify_key({1: "value"}) == "int"
    assert calls == [1, 1]
    assert len(cache) == 2


def test_unordered_nested_dicts_and_sets_have_equivalent_keys() -> None:
    calls: list[int] = []

    @memoize
    def render(value: object) -> object:
        calls.append(1)
        return object()

    first_value: dict[str, object] = {
        "flags": {"red", "blue"},
        "mapping": {"one": [1, 2], "two": (3, 4)},
    }
    second_value: dict[str, object] = {
        "mapping": {"two": (3, 4), "one": [1, 2]},
        "flags": {"blue", "red"},
    }

    assert render(second_value) is render(first_value)
    assert calls == [1]


def test_set_and_frozenset_arguments_have_separate_entries() -> None:
    calls: list[int] = []

    @memoize
    def identify(value: object) -> str:
        calls.append(1)
        return type(value).__name__

    assert identify({1, 2}) == "set"
    assert identify(frozenset({1, 2})) == "frozenset"
    assert calls == [1, 1]


def test_different_decorated_functions_do_not_share_entries() -> None:
    first_calls: list[int] = []
    second_calls: list[int] = []

    @memoize
    def first(value: object) -> str:
        first_calls.append(1)
        return f"first:{value}"

    @memoize
    def second(value: object) -> str:
        second_calls.append(1)
        return f"second:{value}"

    assert first("value") == "first:value"
    assert second("value") == "second:value"
    assert first_calls == [1]
    assert second_calls == [1]
    assert len(cache) == 2


def test_equal_hashable_callable_instances_have_independent_entries() -> None:
    class EqualCallable:
        def __init__(self, label: str) -> None:
            self.label: str = label
            self.calls: int = 0

        def __call__(self, value: int) -> str:
            self.calls += 1
            return f"{self.label}:{value}"

        def __hash__(self) -> int:
            return 1

        def __eq__(self, other: object) -> bool:
            return isinstance(other, EqualCallable)

    first_callable: EqualCallable = EqualCallable("first")
    second_callable: EqualCallable = EqualCallable("second")
    first = memoize(first_callable)
    second = memoize(second_callable)

    assert first(1) == "first:1"
    assert second(1) == "second:1"
    assert first(1) == "first:1"
    assert second(1) == "second:1"
    assert first_callable.calls == 1
    assert second_callable.calls == 1
    assert len(cache) == 2


def test_unhashable_callable_instance_can_be_memoized() -> None:
    @dataclass
    class UnhashableCallable:
        calls: int = 0

        def __call__(self, value: int) -> int:
            self.calls += 1
            return value * 2

    callable_instance: UnhashableCallable = UnhashableCallable()
    decorated = memoize(callable_instance)

    assert decorated(3) == 6
    assert decorated(3) == 6
    assert callable_instance.calls == 1
    assert len(cache) == 1


def test_keyword_argument_order_does_not_affect_cache_key() -> None:
    calls: list[int] = []

    @memoize
    def combine(**values: int) -> object:
        calls.append(1)
        return object()

    first: object = combine(left=1, right=2)
    second: object = combine(right=2, left=1)

    assert second is first
    assert calls == [1]


def test_none_result_is_cached() -> None:
    calls: list[int] = []

    @memoize
    def returns_none(value: object) -> None:
        calls.append(1)

    assert returns_none("value") is None
    assert returns_none("value") is None
    assert calls == [1]
    assert len(cache) == 1


def test_exceptions_are_not_cached() -> None:
    calls: list[int] = []
    error: RuntimeError = RuntimeError("boom")

    @memoize
    def explode(value: object) -> NoReturn:
        calls.append(1)
        raise error

    for _ in range(2):
        with pytest.raises(RuntimeError) as caught:
            explode("value")
        assert caught.value is error

    assert calls == [1, 1]
    assert cache == {}


def test_cyclic_list_raises_exact_error() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)

    @memoize
    def consume(value: object) -> None:
        raise AssertionError("cyclic input must fail before invocation")

    with pytest.raises(ValueError, match=r"^cyclic argument$"):
        consume(cyclic)


def test_cyclic_dict_raises_exact_error() -> None:
    cyclic: dict[str, object] = {}
    cyclic["self"] = cyclic

    @memoize
    def consume(value: object) -> None:
        raise AssertionError("cyclic input must fail before invocation")

    with pytest.raises(ValueError, match=r"^cyclic argument$"):
        consume(cyclic)


def test_shared_noncyclic_reference_is_allowed() -> None:
    shared: list[int] = [1, 2]
    value: list[list[int]] = [shared, shared]
    calls: list[int] = []

    @memoize
    def consume(argument: object) -> str:
        calls.append(1)
        return "ok"

    assert consume(value) == "ok"
    assert consume([[1, 2], [1, 2]]) == "ok"
    assert calls == [1]


def test_unsupported_unhashable_object_names_its_type() -> None:
    @dataclass
    class Unsupported:
        value: int = 0

    @memoize
    def consume(value: object) -> None:
        raise AssertionError("unsupported input must fail before invocation")

    with pytest.raises(
        TypeError,
        match=r"^unsupported unhashable argument: Unsupported$",
    ):
        consume(Unsupported())


def test_hashable_user_objects_are_supported_and_tagged_by_runtime_type() -> None:
    class EqualHash:
        def __hash__(self) -> int:
            return 1

        def __eq__(self, other: object) -> bool:
            return isinstance(other, EqualHash)

    class First(EqualHash):
        pass

    class Second(EqualHash):
        pass

    calls: list[int] = []

    @memoize
    def identify(value: object) -> str:
        calls.append(1)
        return type(value).__name__

    assert identify(First()) == "First"
    assert identify(Second()) == "Second"
    assert calls == [1, 1]


def test_wrapper_preserves_metadata_and_signature() -> None:
    def describe(value: int, *, prefix: str = "value") -> str:
        """Describe a value."""
        return f"{prefix}:{value}"

    describe.category = "example"  # type: ignore[attr-defined]
    decorated = memoize(describe)

    assert decorated.__name__ == "describe"
    assert decorated.__qualname__ == describe.__qualname__
    assert decorated.__doc__ == "Describe a value."
    assert decorated.__module__ == describe.__module__
    assert decorated.__annotations__ == describe.__annotations__
    assert decorated.__dict__["category"] == "example"
    assert decorated.__dict__["__wrapped__"] is describe
    assert signature(decorated) == signature(describe)
