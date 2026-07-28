from collections.abc import ItemsView, KeysView, MutableMapping, ValuesView

import pytest

from .solution_00 import SortedDict


class _FalseyReverseKey:
    def __call__(self, key: int) -> int:
        return -key

    def __bool__(self) -> bool:
        return False


def test_constructs_from_mapping_in_default_key_order() -> None:
    mapping: SortedDict[int, str] = SortedDict[int, str](
        {3: "three", 1: "one", 2: "two"}
    )

    assert list(mapping) == [1, 2, 3]
    assert list(mapping.items()) == [(1, "one"), (2, "two"), (3, "three")]


def test_constructs_from_iterable_pairs() -> None:
    mapping: SortedDict[str, int] = SortedDict[str, int](
        [("charlie", 3), ("alpha", 1), ("bravo", 2)]
    )

    assert list(mapping.items()) == [("alpha", 1), ("bravo", 2), ("charlie", 3)]


def test_constructs_empty_mapping() -> None:
    mapping: SortedDict[str, int] = SortedDict[str, int]()

    assert len(mapping) == 0
    assert list(mapping) == []


def test_mutations_are_sorted_live_by_key_length() -> None:
    mapping: SortedDict[str, int] = SortedDict[str, int](
        {"three": 3, "one": 1}, keyfunc=len
    )
    keys_view: KeysView[str] = mapping.keys()
    items_view: ItemsView[str, int] = mapping.items()
    values_view: ValuesView[int] = mapping.values()

    mapping["to"] = 2
    mapping["f"] = 1

    assert list(keys_view) == ["f", "to", "one", "three"]
    assert list(items_view) == [
        ("f", 1),
        ("to", 2),
        ("one", 1),
        ("three", 3),
    ]
    assert list(values_view) == [1, 2, 1, 3]


def test_deletion_and_repr_follow_sorted_order() -> None:
    mapping: SortedDict[str, int] = SortedDict[str, int](
        [("three", 3), ("to", 2), ("f", 1)], len
    )

    del mapping["to"]

    assert repr(mapping) == "SortedDict({'f': 1, 'three': 3})"


def test_repr_handles_self_reference() -> None:
    mapping: SortedDict[str, object] = SortedDict[str, object]()
    mapping["self"] = mapping

    assert repr(mapping) == "SortedDict({'self': ...})"


def test_replacing_value_does_not_duplicate_key() -> None:
    mapping: SortedDict[str, int] = SortedDict[str, int]([("b", 1), ("a", 2)])

    mapping["a"] = 10

    assert len(mapping) == 2
    assert list(mapping.items()) == [("a", 10), ("b", 1)]


def test_falsey_custom_key_can_reverse_numeric_order() -> None:
    mapping: SortedDict[int, str] = SortedDict[int, str](
        [(1, "one"), (3, "three"), (2, "two")],
        keyfunc=_FalseyReverseKey(),
    )

    assert list(mapping) == [3, 2, 1]


def test_missing_key_access_raises_key_error() -> None:
    mapping: SortedDict[str, int] = SortedDict[str, int]()

    with pytest.raises(KeyError, match="missing"):
        _ = mapping["missing"]


def test_missing_key_deletion_raises_key_error() -> None:
    mapping: SortedDict[str, int] = SortedDict[str, int]()

    with pytest.raises(KeyError, match="missing"):
        del mapping["missing"]


def test_mutable_mapping_equality_ignores_iteration_order() -> None:
    mapping: MutableMapping[str, int] = SortedDict[str, int](
        [("long", 2), ("x", 1)], keyfunc=len
    )

    assert mapping == {"x": 1, "long": 2}
    assert {"long": 2, "x": 1} == mapping
