"""Safely complete mapping keys and finite-sequence indices."""

from __future__ import annotations

import ast
import inspect
import rlcompleter
import sys
from collections.abc import Hashable, Iterator, Mapping, Sequence
from typing import Final, cast

MAX_MATCHES: Final[int] = 25
_UNRESOLVED: Final[object] = object()


class Completer(rlcompleter.Completer):
    """Extend standard completion with safe item completion."""

    def __init__(self, namespace: Mapping[str, object] | None = None) -> None:
        parent_namespace: dict[str, object] | None = (
            dict(namespace) if namespace is not None else None
        )
        super().__init__(parent_namespace)
        self._namespace: Mapping[str, object] | None = namespace
        self._item_completion_active: bool = False
        self._item_matches_cache: list[str] = []

    def _active_namespace(self) -> Mapping[str, object]:
        if self._namespace is None:
            return cast(Mapping[str, object], vars(sys.modules["__main__"]))
        return self._namespace

    def _resolve_node(self, node: ast.expr) -> object:
        if isinstance(node, ast.Name):
            namespace: Mapping[str, object] = self._active_namespace()
            if node.id not in namespace:
                return _UNRESOLVED
            return namespace[node.id]

        if isinstance(node, ast.Attribute):
            owner: object = self._resolve_node(node.value)
            if owner is _UNRESOLVED:
                return _UNRESOLVED
            try:
                attribute: object = inspect.getattr_static(owner, node.attr)
            except AttributeError:
                return _UNRESOLVED
            return attribute

        if isinstance(node, ast.Subscript):
            container: object = self._resolve_node(node.value)
            if container is _UNRESOLVED:
                return _UNRESOLVED
            try:
                key: object = ast.literal_eval(node.slice)
            except (SyntaxError, ValueError):
                return _UNRESOLVED
            if not isinstance(key, Hashable):
                return _UNRESOLVED
            try:
                if isinstance(container, Mapping):
                    mapping: Mapping[object, object] = cast(
                        Mapping[object, object], container
                    )
                    return mapping[key]
                if (
                    isinstance(container, (list, tuple, str))
                    and isinstance(key, int)
                    and not isinstance(key, bool)
                ):
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
        if isinstance(value, Mapping):
            mapping: Mapping[object, object] = cast(Mapping[object, object], value)
            keys: Iterator[object] = iter(mapping)
        elif isinstance(value, (list, tuple, str)):
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
            if self._matches_prefix(key, prefix.lstrip()):
                yield f"{expression}[{key!r}]"

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
        return super().complete(text, state)


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
