"""Search raw input stored in IPython history."""

from __future__ import annotations

import argparse
import re
import sqlite3
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass
from typing import cast

from IPython.core.history import HistoryAccessor


class HistoryAccessError(RuntimeError):
    """IPython's default history accessor could not be created."""


@dataclass(frozen=True)
class HistoryMatch:
    """One matching input from an IPython session."""

    session: int
    line: int
    source: str

    def _location(self) -> tuple[int, int]:
        return (self.session, self.line)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, HistoryMatch):
            return NotImplemented
        return self._location() < other._location()

    def __le__(self, other: object) -> bool:
        if not isinstance(other, HistoryMatch):
            return NotImplemented
        return self._location() <= other._location()

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, HistoryMatch):
            return NotImplemented
        return self._location() > other._location()

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, HistoryMatch):
            return NotImplemented
        return self._location() >= other._location()


def search_history(
    pattern: str,
    records: Iterable[tuple[int, int, str]],
) -> list[HistoryMatch]:
    """Return saved inputs matching *pattern*, ordered by session and line."""
    expression: re.Pattern[str] = re.compile(pattern)
    return sorted(
        HistoryMatch(session, line, source)
        for session, line, source in records
        if expression.search(source)
    )


def format_history_match(match: HistoryMatch) -> str:
    """Frame every source line with its saved location."""
    prefix: str = f"{match.session}:{match.line}: "
    source_lines: list[str] = match.source.split("\n")
    framed_lines: list[str] = [f"{prefix}{source_lines[0]}"]
    framed_lines.extend(f"{prefix}| {line}" for line in source_lines[1:])
    return "\n".join(framed_lines)


def iter_ipython_history(
    accessor: HistoryAccessor | None = None,
) -> Iterator[tuple[int, int, str]]:
    """Yield raw stored input from every IPython session."""
    owns_accessor: bool = accessor is None
    accessor_factory: Callable[[], HistoryAccessor] = cast(
        Callable[[], HistoryAccessor], HistoryAccessor
    )
    if accessor is not None:
        history: HistoryAccessor = accessor
    else:
        try:
            history = accessor_factory()
        except OSError as error:
            raise HistoryAccessError(str(error)) from error
    try:
        records: Iterator[tuple[int, int, str]] = cast(
            Iterator[tuple[int, int, str]],
            history.search("*", raw=True, search_raw=True, unique=False),
        )
        yield from records
    finally:
        if owns_accessor:
            connection: sqlite3.Connection = cast(
                sqlite3.Connection,
                history.db,  # pyright: ignore[reportUnknownMemberType]
            )
            connection.close()


def main(argv: Sequence[str] | None = None) -> int:
    """Search IPython history for one regular expression."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Search raw input from all saved IPython sessions."
    )
    parser.add_argument("pattern", help="Python regular expression to search for")
    arguments: argparse.Namespace = parser.parse_args(argv)
    pattern: str = cast(str, arguments.pattern)

    try:
        matches: list[HistoryMatch] = search_history(pattern, iter_ipython_history())
    except re.error as error:
        parser.error(f"invalid regular expression: {error}")
    except HistoryAccessError as error:
        parser.error(f"unable to open IPython history: {error}")
    for match in matches:
        print(format_history_match(match))
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
