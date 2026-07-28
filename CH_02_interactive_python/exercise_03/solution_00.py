"""Complete Python source statically with Jedi."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, cast

import jedi  # type: ignore[import-untyped]


class _Completion(Protocol):
    @property
    def name_with_symbols(self) -> str: ...


class _Script(Protocol):
    def complete(self, line: int, column: int) -> Iterable[_Completion]: ...


def complete_source(
    source: str,
    *,
    line: int | None = None,
    column: int | None = None,
) -> list[str]:
    """Return Jedi completion spellings at a validated source position."""
    lines: list[str] = source.splitlines()
    if not lines or source.endswith(("\r", "\n")):
        lines.append("")
    selected_line: int = len(lines) if line is None else line
    if not 1 <= selected_line <= len(lines):
        raise ValueError(
            f"line must be between 1 and {len(lines)}; got {selected_line}",
        )

    selected_source_line: str = lines[selected_line - 1]
    selected_column: int = len(selected_source_line) if column is None else column
    if not 0 <= selected_column <= len(selected_source_line):
        raise ValueError(
            "column must be between 0 and "
            f"{len(selected_source_line)} for line {selected_line}; "
            f"got {selected_column}",
        )

    script: _Script = cast(_Script, jedi.Script(code=source))
    completions: Iterable[_Completion] = script.complete(
        selected_line,
        selected_column,
    )
    names: set[str] = {completion.name_with_symbols for completion in completions}
    return sorted(names)


def _demo() -> None:
    source: str = "from pathlib import Pa"
    print("\n".join(complete_source(source)))


if __name__ == "__main__":
    _demo()
