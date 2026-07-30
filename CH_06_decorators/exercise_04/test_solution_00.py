"""Tests for per-function memoization caches."""

import inspect
from dataclasses import dataclass
from typing import NoReturn

import pytest

from . import solution_00
from .solution_00 import memoize


def test_public_api_exposes_memoized_callable_protocol() -> None:
    assert hasattr(solution_00, "MemoizedCallable")


def test_decorated_functions_own_distinct_caches() -> None:
    first_calls: list[int] = []
    second_calls: list[int] = []

    @memoize
    def first(value: int) -> str:
        first_calls.append(value)
        return f"first:{value}"

    @memoize
    def second(value: int) -> str:
        second_calls.append(value)
        return f"second:{value}"

    assert first.cache is not second.cache
    assert first(1) == "first:1"
    assert second(1) == "second:1"
    assert first(1) == "first:1"
    assert second(1) == "second:1"
    assert first_calls == [1]
    assert second_calls == [1]
    assert len(first.cache) == 1
    assert len(second.cache) == 1


def test_equivalent_mutable_arguments_and_reordered_keywords_hit_cache() -> None:
    calls: list[int] = []

    @memoize
    def render(values: object, **options: object) -> object:
        calls.append(1)
        return object()

    first: object = render(
        [{"labels": {"beta", "alpha"}}],
        enabled=True,
        settings={"scale": [1, 2]},
    )
    second: object = render(
        [{"labels": {"alpha", "beta"}}],
        settings={"scale": [1, 2]},
        enabled=True,
    )

    assert second is first
    assert calls == [1]
    assert len(render.cache) == 1


def test_cache_clear_is_local_and_forces_recomputation() -> None:
    first_calls: list[int] = []
    second_calls: list[int] = []

    @memoize
    def first(value: int) -> object:
        first_calls.append(value)
        return object()

    @memoize
    def second(value: int) -> object:
        second_calls.append(value)
        return object()

    first_result: object = first(1)
    second_result: object = second(1)
    first.cache_clear()

    assert first.cache == {}
    assert len(second.cache) == 1
    assert first(1) is not first_result
    assert second(1) is second_result
    assert first_calls == [1, 1]
    assert second_calls == [1]


def test_none_result_is_cached() -> None:
    calls: list[int] = []

    @memoize
    def returns_none(value: object) -> None:
        calls.append(1)

    assert returns_none("value") is None
    assert returns_none("value") is None
    assert calls == [1]
    assert len(returns_none.cache) == 1


def test_exceptions_are_not_cached() -> None:
    calls: list[int] = []

    @memoize
    def fail(value: object) -> NoReturn:
        calls.append(1)
        raise RuntimeError("boom")

    for _ in range(2):
        with pytest.raises(RuntimeError, match=r"^boom$"):
            fail("value")

    assert calls == [1, 1]
    assert fail.cache == {}


def test_container_and_scalar_runtime_types_have_distinct_entries() -> None:
    calls: list[str] = []

    @memoize
    def identify(value: object) -> str:
        name: str = type(value).__name__
        calls.append(name)
        return name

    arguments: list[object] = [
        [1, 2],
        (1, 2),
        True,
        1,
        {1, 2},
        frozenset({1, 2}),
    ]
    expected: list[str] = ["list", "tuple", "bool", "int", "set", "frozenset"]

    assert [identify(value) for value in arguments] == expected
    assert [identify(value) for value in arguments] == expected
    assert calls == expected
    assert len(identify.cache) == 6


def test_nested_unordered_containers_are_order_independent() -> None:
    calls: list[int] = []

    @memoize
    def consume(value: object) -> object:
        calls.append(1)
        return object()

    first: object = consume(
        {
            "groups": [
                {"members": {"Ada", "Grace"}},
                {"members": frozenset({"Linus", "Guido"})},
            ]
        }
    )
    second: object = consume(
        {
            "groups": [
                {"members": {"Grace", "Ada"}},
                {"members": frozenset({"Guido", "Linus"})},
            ]
        }
    )

    assert second is first
    assert calls == [1]


def test_cyclic_list_raises_exact_error() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)

    @memoize
    def consume(value: object) -> object:
        return value

    with pytest.raises(ValueError, match=r"^cyclic argument$"):
        consume(cyclic)


def test_cyclic_dict_raises_exact_error() -> None:
    cyclic: dict[str, object] = {}
    cyclic["self"] = cyclic

    @memoize
    def consume(value: object) -> object:
        return value

    with pytest.raises(ValueError, match=r"^cyclic argument$"):
        consume(cyclic)


def test_shared_noncyclic_reference_is_supported() -> None:
    calls: list[int] = []
    shared: list[int] = [1, 2]

    @memoize
    def consume(value: object) -> object:
        calls.append(1)
        return object()

    first: object = consume([shared, shared])
    second: object = consume([[1, 2], [1, 2]])

    assert second is first
    assert calls == [1]


def test_unsupported_unhashable_argument_raises_exact_error() -> None:
    @dataclass
    class Unsupported:
        value: int

    @memoize
    def consume(value: object) -> object:
        return value

    with pytest.raises(
        TypeError,
        match=r"^unsupported unhashable argument: Unsupported$",
    ):
        consume(Unsupported(1))


def test_metadata_custom_attributes_wrapping_and_signature_are_preserved() -> None:
    def original(prefix: str, /, value: int = 1, *, suffix: str) -> str:
        """Build a labelled value."""
        return f"{prefix}{value}{suffix}"

    vars(original)["category"] = "formatter"
    original_signature: inspect.Signature = inspect.signature(original)
    decorated = memoize(original)

    assert decorated("value=", value=2, suffix="!") == "value=2!"
    assert decorated.__name__ == "original"
    assert decorated.__doc__ == "Build a labelled value."
    assert vars(decorated)["category"] == "formatter"
    assert decorated.__wrapped__ is original
    assert inspect.signature(decorated) == original_signature


def test_cache_is_live_inspectable_dictionary() -> None:
    calls: list[int] = []

    @memoize
    def calculate(value: int) -> int:
        calls.append(value)
        return value * 2

    exposed_cache = calculate.cache

    assert isinstance(exposed_cache, dict)
    assert exposed_cache == {}
    assert calculate(3) == 6
    assert calculate.cache is exposed_cache
    assert len(exposed_cache) == 1
    exposed_cache.clear()
    assert calculate(3) == 6
    assert calls == [3, 3]
