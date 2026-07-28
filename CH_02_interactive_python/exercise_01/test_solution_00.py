"""Tests for the safe item completer."""

import importlib
import readline
import rlcompleter
from collections.abc import Mapping
from types import MappingProxyType, ModuleType, SimpleNamespace

import pytest

from . import solution_00
from .solution_00 import MAX_MATCHES, Completer


def test_completes_mapping_keys_using_repr() -> None:
    values: Mapping[object, object] = MappingProxyType(
        {"alpha": 1, "beta": 2, 10: "ten"}
    )
    completer: Completer = Completer({"values": values})

    matches: list[str] = list(completer.item_matches("values["))

    assert matches == ["values['alpha']", "values['beta']", "values[10]"]


def test_filters_mapping_keys_by_quoted_and_unquoted_prefixes() -> None:
    values: dict[object, object] = {"alpha": 1, "beta": 2, 10: "ten", 20: "twenty"}
    completer: Completer = Completer({"values": values})

    quoted_matches: list[str] = list(completer.item_matches("values['a"))
    numeric_matches: list[str] = list(completer.item_matches("values[1"))

    assert quoted_matches == ["values['alpha']"]
    assert numeric_matches == ["values[10]"]


def test_completes_list_tuple_and_string_indices() -> None:
    namespace: dict[str, object] = {
        "items": ["first", "second"],
        "pair": ("left", "right"),
        "word": "abc",
    }
    completer: Completer = Completer(namespace)

    list_matches: list[str] = list(completer.item_matches("items["))
    tuple_matches: list[str] = list(completer.item_matches("pair["))
    string_matches: list[str] = list(completer.item_matches("word["))

    assert list_matches == ["items[0]", "items[1]"]
    assert tuple_matches == ["pair[0]", "pair[1]"]
    assert string_matches == ["word[0]", "word[1]", "word[2]"]


def test_filters_sequence_indices_by_prefix() -> None:
    items: list[int] = list(range(20))
    completer: Completer = Completer({"items": items})

    matches: list[str] = list(completer.item_matches("items[1"))

    assert matches == [
        "items[1]",
        "items[10]",
        "items[11]",
        "items[12]",
        "items[13]",
        "items[14]",
        "items[15]",
        "items[16]",
        "items[17]",
        "items[18]",
        "items[19]",
    ]


def test_resolves_attributes_and_literal_subscripts() -> None:
    holder: SimpleNamespace = SimpleNamespace(values={"nested": ["a", "b"]})
    completer: Completer = Completer({"holder": holder})

    attribute_matches: list[str] = list(completer.item_matches("holder.values["))
    nested_matches: list[str] = list(completer.item_matches("holder.values['nested']["))

    assert attribute_matches == ["holder.values['nested']"]
    assert nested_matches == [
        "holder.values['nested'][0]",
        "holder.values['nested'][1]",
    ]


def test_missing_and_unsupported_values_have_no_item_matches() -> None:
    namespace: dict[str, object] = {"number": 42, "items": {1, 2, 3}}
    completer: Completer = Completer(namespace)

    missing_matches: list[str] = list(completer.item_matches("missing["))
    scalar_matches: list[str] = list(completer.item_matches("number["))
    set_matches: list[str] = list(completer.item_matches("items["))
    unsupported_expression_matches: list[str] = list(
        completer.item_matches("(number + 1)[")
    )

    assert missing_matches == []
    assert scalar_matches == []
    assert set_matches == []
    assert unsupported_expression_matches == []


def test_caps_item_matches_at_max_matches() -> None:
    values: dict[str, int] = {f"key-{index}": index for index in range(30)}
    completer: Completer = Completer({"values": values})

    matches: list[str] = list(completer.item_matches("values["))

    assert MAX_MATCHES == 25
    assert len(matches) == MAX_MATCHES
    assert matches[-1] == "values['key-24']"


def test_does_not_invoke_call_expressions() -> None:
    calls: list[str] = []

    def dangerous() -> dict[str, int]:
        calls.append("called")
        return {"secret": 1}

    completer: Completer = Completer({"dangerous": dangerous})

    matches: list[str] = list(completer.item_matches("dangerous()["))

    assert matches == []
    assert calls == []


def test_complete_caches_item_matches_across_states() -> None:
    completer: Completer = Completer({"values": {"alpha": 1, "beta": 2}})

    first: str | None = completer.complete("values[", 0)
    second: str | None = completer.complete("values[", 1)
    exhausted: str | None = completer.complete("values[", 2)

    assert first == "values['alpha']"
    assert second == "values['beta']"
    assert exhausted is None


def test_complete_resets_cached_matches_at_state_zero() -> None:
    completer: Completer = Completer({"values": {"alpha": 1, "beta": 2}})

    initial: str | None = completer.complete("values[", 0)
    reset: str | None = completer.complete("values['b", 0)
    exhausted: str | None = completer.complete("values['b", 1)

    assert initial == "values['alpha']"
    assert reset == "values['beta']"
    assert exhausted is None


def test_complete_delegates_normal_name_completion() -> None:
    completer: Completer = Completer({"example_name": 1})

    match: str | None = completer.complete("example_n", 0)

    assert match == "example_name"


def test_complete_delegates_item_text_without_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, int]] = []

    def standard_complete(
        completer: rlcompleter.Completer, text: str, state: int
    ) -> str | None:
        del completer
        calls.append((text, state))
        return f"standard-{state}"

    monkeypatch.setattr(rlcompleter.Completer, "complete", standard_complete)
    completer: Completer = Completer({"number": 42})

    first: str | None = completer.complete("number[", 0)
    second: str | None = completer.complete("number[", 1)

    assert first == "standard-0"
    assert second == "standard-1"
    assert calls == [("number[", 0), ("number[", 1)]


def test_import_does_not_register_readline_hooks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []

    def record_completer(completer: object) -> None:
        calls.append(("set_completer", completer))

    def record_parse_and_bind(command: str) -> None:
        calls.append(("parse_and_bind", command))

    monkeypatch.setattr(readline, "set_completer", record_completer)
    monkeypatch.setattr(readline, "parse_and_bind", record_parse_and_bind)

    reloaded: ModuleType = importlib.reload(solution_00)

    assert reloaded is solution_00
    assert calls == []
