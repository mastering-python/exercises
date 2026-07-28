"""Tests for the safe item completer."""

import importlib
import readline
import rlcompleter
from collections.abc import Iterator, Mapping
from types import ModuleType, SimpleNamespace
from typing import ClassVar, cast

import pytest

from . import solution_00
from .solution_00 import MAX_MATCHES, Completer


class RecordingMapping(Mapping[object, object]):
    def __init__(self, calls: list[str]) -> None:
        self._calls: list[str] = calls

    def __getitem__(self, key: object) -> object:
        self._calls.append("getitem")
        raise KeyError(key)

    def __iter__(self) -> Iterator[object]:
        self._calls.append("iter")
        return iter(())

    def __len__(self) -> int:
        self._calls.append("len")
        return 0


class RecordingKey:
    def __init__(self, calls: list[str]) -> None:
        self._calls: list[str] = calls

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        self._calls.append("repr")
        return "unsafe_key"


class RecordingNamespaceKey:
    def __init__(self, calls: list[str]) -> None:
        self._calls: list[str] = calls

    def __hash__(self) -> int:
        return hash("values")

    def __eq__(self, other: object) -> bool:
        del other
        self._calls.append("eq")
        return False


class RecordingList(list[object]):
    def __init__(self, calls: list[str]) -> None:
        super().__init__(["unsafe"])
        self._calls: list[str] = calls

    def __len__(self) -> int:
        self._calls.append("len")
        return super().__len__()


def test_completes_mapping_keys_using_repr() -> None:
    values: Mapping[object, object] = {"alpha": 1, "beta": 2, 10: "ten"}
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


def test_rejects_non_finite_float_and_complex_keys() -> None:
    values: dict[object, object] = {
        1.5: "finite float",
        float("inf"): "positive infinity",
        float("-inf"): "negative infinity",
        float("nan"): "not a number",
        complex(1, 2): "finite complex",
        complex(float("inf"), 1): "infinite real component",
        complex(1, float("nan")): "nan imaginary component",
    }
    completer: Completer = Completer({"values": values})

    matches: list[str] = list(completer.item_matches("values["))

    assert matches == ["values[1.5]", "values[(1+2j)]"]


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


def test_complete_does_not_invoke_properties() -> None:
    calls: list[str] = []

    class Dangerous:
        @property
        def secret(self) -> dict[str, int]:
            calls.append("property")
            return {"secret": 1}

    completer: Completer = Completer({"dangerous": Dangerous()})

    match: str | None = completer.complete("dangerous.secret.", 0)

    assert calls == []
    assert match is None


def test_complete_does_not_inspect_class_roots_with_hostile_metaclasses() -> None:
    calls: list[str] = []

    class HostileMeta(type):
        def __getattribute__(cls, name: str) -> object:
            calls.append(name)
            return super().__getattribute__(name)

    class Evil(metaclass=HostileMeta):
        values: ClassVar[dict[str, int]] = {"secret": 1}

    completer: Completer = Completer({"Evil": Evil})

    match: str | None = completer.complete("Evil.values[", 0)

    assert calls == []
    assert match is None


def test_complete_does_not_inspect_instances_with_hostile_metaclasses() -> None:
    calls: list[str] = []

    class HostileMeta(type):
        def __getattribute__(cls, name: str) -> object:
            calls.append(name)
            return super().__getattribute__(name)

    class Evil(metaclass=HostileMeta):
        values: dict[str, int]

        def __init__(self) -> None:
            self.values = {"secret": 1}

    evil: Evil = Evil()
    calls.clear()
    completer: Completer = Completer({"obj": evil})

    match: str | None = completer.complete("obj.values[", 0)

    assert calls == []
    assert match is None


def test_complete_does_not_inspect_hostile_instances_from_safe_containers() -> None:
    calls: list[str] = []

    class HostileMeta(type):
        def __getattribute__(cls, name: str) -> object:
            calls.append(name)
            return super().__getattribute__(name)

    class Evil(metaclass=HostileMeta):
        values: dict[str, int]

        def __init__(self) -> None:
            self.values = {"secret": 1}

    evil: Evil = Evil()
    calls.clear()
    namespace: dict[str, object] = {
        "objects": {"evil": evil},
        "items": [evil],
        "pair": (evil,),
    }
    completer: Completer = Completer(namespace)

    expression: str
    for expression in (
        "objects['evil'].values[",
        "items[0].values[",
        "pair[0].values[",
    ):
        match: str | None = completer.complete(expression, 0)

        assert calls == []
        assert match is None


def test_name_completion_does_not_inspect_callable_objects() -> None:
    calls: list[str] = []

    class DangerousCallable:
        @property
        def __signature__(self) -> object:
            calls.append("signature")
            return None

        def __call__(self) -> None:
            calls.append("call")

    completer: Completer = Completer({"dangerous_callable": DangerousCallable()})

    match: str | None = completer.complete("dangerous_c", 0)

    assert calls == []
    assert match == "dangerous_callable"


def test_item_completion_does_not_iterate_custom_mappings() -> None:
    calls: list[str] = []
    completer: Completer = Completer({"values": RecordingMapping(calls)})

    match: str | None = completer.complete("values[", 0)

    assert match is None
    assert calls == []


def test_nested_item_completion_does_not_index_custom_mappings() -> None:
    calls: list[str] = []
    completer: Completer = Completer({"values": RecordingMapping(calls)})

    match: str | None = completer.complete("values['nested'][", 0)

    assert match is None
    assert calls == []


def test_item_completion_does_not_render_unsafe_keys() -> None:
    calls: list[str] = []
    key: RecordingKey = RecordingKey(calls)
    completer: Completer = Completer({"values": {key: "secret"}})

    match: str | None = completer.complete("values[", 0)

    assert match is None
    assert calls == []


def test_item_completion_rejects_container_subclasses_without_invoking_them() -> None:
    calls: list[str] = []
    completer: Completer = Completer({"values": RecordingList(calls)})

    match: str | None = completer.complete("values[", 0)

    assert match is None
    assert calls == []


def test_namespace_snapshot_is_shared_by_all_completion_paths() -> None:
    namespace: dict[str, object] = {"values": {"before": 1}}
    completer: Completer = Completer(namespace)
    namespace["values"] = {"after": 2}

    matches: list[str] = list(completer.item_matches("values["))

    assert matches == ["values['before']"]


def test_item_completion_does_not_compare_unsafe_namespace_keys() -> None:
    calls: list[str] = []
    key: RecordingNamespaceKey = RecordingNamespaceKey(calls)
    unsafe_namespace: dict[object, object] = {key: {"secret": 1}}
    namespace: Mapping[str, object] = cast(Mapping[str, object], unsafe_namespace)
    completer: Completer = Completer(namespace)

    match: str | None = completer.complete("values[", 0)

    assert calls == []
    assert match is None


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


def test_complete_preserves_explicit_namespace_completion() -> None:
    completer: Completer = Completer({"example_name": 1})

    match: str | None = completer.complete("example_n", 0)

    assert match == "example_name"


def test_complete_preserves_builtin_name_completion() -> None:
    completer: Completer = Completer({})

    match: str | None = completer.complete("pri", 0)

    assert match == "print("


def test_complete_preserves_keyword_completion() -> None:
    completer: Completer = Completer({})

    match: str | None = completer.complete("for", 0)

    assert match == "for "


@pytest.mark.parametrize("name", ["_", "case", "match"])
def test_complete_treats_soft_keywords_as_namespace_names(name: str) -> None:
    completer: Completer = Completer({name: 1})

    match: str | None = completer.complete(name, 0)

    assert match == name


def test_complete_does_not_delegate_item_text_without_matches(
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

    assert first is None
    assert second is None
    assert calls == []


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
