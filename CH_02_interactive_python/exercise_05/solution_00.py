"""Search raw input stored in IPython history."""

from __future__ import annotations

import argparse
import re
import sqlite3
from collections.abc import Callable, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from typing import cast

from IPython.core.history import HistoryAccessor


@dataclass(frozen=True, order=True)
class HistoryMatch:
    """One matching input from an IPython session."""

    session: int
    line: int
    source: str = field(compare=False)


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


def iter_ipython_history(
    accessor: HistoryAccessor | None = None,
) -> Iterator[tuple[int, int, str]]:
    """Yield raw stored input from every IPython session."""
    owns_accessor: bool = accessor is None
    accessor_factory: Callable[[], HistoryAccessor] = cast(
        Callable[[], HistoryAccessor], HistoryAccessor
    )
    history: HistoryAccessor = accessor if accessor is not None else accessor_factory()
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

    matches: list[HistoryMatch] = search_history(pattern, iter_ipython_history())
    for match in matches:
        print(f"{match.session}:{match.line}: {match.source}")
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
