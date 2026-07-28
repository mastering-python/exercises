"""Safely complete mapping keys and finite-sequence indices."""

from __future__ import annotations

import ast
import builtins
import inspect
import keyword
import math
import rlcompleter
import sys
from collections.abc import Iterator, Mapping, Sequence
from typing import Final, cast

MAX_MATCHES: Final[int] = 25
_UNRESOLVED: Final[object] = object()
_KEYWORDS: Final[tuple[str, ...]] = (*keyword.kwlist, *keyword.softkwlist)
_BUILTINS: Final[tuple[tuple[str, object], ...]] = tuple(
    (name, value) for name, value in vars(builtins).items() if type(name) is str
)


def _is_safe_literal(value: object) -> bool:
    value_type: type[object] = type(value)
    if value_type in (str, bytes, int, bool, type(None)):
        return True
    if value_type is float:
        float_number: float = cast(float, value)
        return math.isfinite(float_number)
    if value_type is complex:
        complex_number: complex = cast(complex, value)
        return math.isfinite(complex_number.real) and math.isfinite(complex_number.imag)
    if value_type is tuple:
        items: tuple[object, ...] = cast(tuple[object, ...], value)
        return all(_is_safe_literal(item) for item in items)
    return False


def _is_safe_container(value: object) -> bool:
    return type(value) in (dict, list, tuple, str)


class Completer(rlcompleter.Completer):
    """Extend standard completion with safe item completion."""

    def __init__(self, namespace: Mapping[str, object] | None = None) -> None:
        parent_namespace: dict[str, object] | None = (
            dict(namespace) if namespace is not None else None
        )
        super().__init__(parent_namespace)
        self._namespace: Mapping[str, object] | None = parent_namespace
        self._item_completion_active: bool = False
        self._item_matches_cache: list[str] = []
        self._name_matches_cache: list[str] = []

    def _active_namespace(self) -> Mapping[str, object]:
        if self._namespace is None:
            return cast(Mapping[str, object], vars(sys.modules["__main__"]))
        return self._namespace

    def _resolve_name(self, name: str) -> object:
        candidate: object
        value: object
        for candidate, value in self._active_namespace().items():
            if type(candidate) is str and candidate == name:
                return value
        return _UNRESOLVED

    def _resolve_node(self, node: ast.expr) -> object:
        if isinstance(node, ast.Name):
            return self._resolve_name(node.id)

        if isinstance(node, ast.Attribute):
            owner: object = self._resolve_node(node.value)
            if owner is _UNRESOLVED:
                return _UNRESOLVED
            if isinstance(owner, type):
                return _UNRESOLVED
            try:
                attribute: object = inspect.getattr_static(owner, node.attr)
            except AttributeError:
                return _UNRESOLVED
            if _is_safe_container(attribute):
                return attribute
            return _UNRESOLVED

        if isinstance(node, ast.Subscript):
            container: object = self._resolve_node(node.value)
            if container is _UNRESOLVED:
                return _UNRESOLVED
            try:
                key: object = ast.literal_eval(node.slice)
            except (SyntaxError, ValueError):
                return _UNRESOLVED
            if not _is_safe_literal(key):
                return _UNRESOLVED
            try:
                if type(container) is dict:
                    mapping: Mapping[object, object] = cast(
                        Mapping[object, object], container
                    )
                    for candidate, value in mapping.items():
                        if _is_safe_literal(candidate) and candidate == key:
                            return value
                    return _UNRESOLVED
                if type(container) in (list, tuple, str) and type(key) is int:
                    sequence: Sequence[object] = cast(Sequence[object], container)
                    return sequence[key]
            except (IndexError, KeyError, TypeError):
                return _UNRESOLVED

        return _UNRESOLVED

    def _resolve_expression(self, expression: str) -> object:
        try:
            node: ast.expr = ast.parse(expression, mode="eval").body
        except SyntaxError:
            return _UNRESOLVED
        return self._resolve_node(node)

    @staticmethod
    def _matches_prefix(key: object, prefix: str) -> bool:
        if not prefix:
            return True
        if prefix[0] in {"'", '"'}:
            return isinstance(key, str) and key.startswith(prefix[1:])
        return repr(key).startswith(prefix)

    def item_matches(self, text: str) -> Iterator[str]:
        """Yield safe item completions for the final opening bracket in *text*."""
        expression: str
        separator: str
        prefix: str
        expression, separator, prefix = text.rpartition("[")
        if not separator or not expression:
            return

        value: object = self._resolve_expression(expression)
        if type(value) is dict:
            mapping: Mapping[object, object] = cast(Mapping[object, object], value)
            keys: Iterator[object] = iter(mapping)
        elif type(value) in (list, tuple, str):
            sequence: Sequence[object] = cast(Sequence[object], value)
            keys = iter(range(min(len(sequence), MAX_MATCHES)))
        else:
            return

        inspected: int = 0
        key: object
        for key in keys:
            if inspected >= MAX_MATCHES:
                return
            inspected += 1
            if not _is_safe_literal(key):
                continue
            if self._matches_prefix(key, prefix.lstrip()):
                yield f"{expression}[{key!r}]"

    def _name_matches(self, text: str) -> Iterator[str]:
        if not text.isidentifier():
            return
        seen: set[str] = set()
        keyword_name: str
        for keyword_name in _KEYWORDS:
            if keyword_name.startswith(text):
                seen.add(keyword_name)
                if keyword_name in {"finally", "try"}:
                    yield f"{keyword_name}:"
                elif keyword_name in {"False", "None", "True"}:
                    yield keyword_name
                else:
                    yield f"{keyword_name} "
        name: object
        for name in self._active_namespace():
            if type(name) is str and name not in seen and name.startswith(text):
                seen.add(name)
                yield name
        value: object
        for name, value in _BUILTINS:
            if name in seen or not name.startswith(text):
                continue
            if type(value) in (type(len), type):
                yield f"{name}("
            else:
                yield name

    def complete(self, text: str, state: int) -> str | None:
        """Return the requested cached item match or standard completion."""
        if "[" in text:
            if state == 0:
                self._item_matches_cache = list(self.item_matches(text))
                self._item_completion_active = bool(self._item_matches_cache)
            if self._item_completion_active:
                try:
                    return self._item_matches_cache[state]
                except IndexError:
                    return None
            return None
        if "." in text:
            return None
        if state == 0:
            self._name_matches_cache = list(self._name_matches(text))
        try:
            return self._name_matches_cache[state]
        except IndexError:
            return None


def main() -> None:
    """Print a small, non-registering completion demonstration."""
    namespace: dict[str, object] = {
        "config": {"host": "localhost", "port": 8000},
        "letters": ["a", "b", "c"],
    }
    completer: Completer = Completer(namespace)
    text: str
    for text in ("config[", "letters["):
        matches: list[str] = list(completer.item_matches(text))
        print(f"{text} -> {matches}")


if __name__ == "__main__":
    main()
