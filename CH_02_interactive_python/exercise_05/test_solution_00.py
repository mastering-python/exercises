"""Tests for searching saved IPython history."""

from __future__ import annotations

import re
import sqlite3
import subprocess
import sys
from collections.abc import Callable, Generator, Iterator
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import cast

import pytest
from IPython.core.history import HistoryAccessor

import CH_02_interactive_python.exercise_05.solution_00 as solution_00

from .solution_00 import HistoryMatch, iter_ipython_history, main, search_history


class _OneShotHistory:
    def __init__(self, records: list[tuple[int, int, str]]) -> None:
        self._records: list[tuple[int, int, str]] = records
        self._iterated: bool = False

    def __iter__(self) -> Iterator[tuple[int, int, str]]:
        if self._iterated:
            raise AssertionError("history was consumed more than once")
        self._iterated = True
        return iter(self._records)


class _FakeConnection:
    def __init__(self) -> None:
        self.close_calls: int = 0

    def close(self) -> None:
        self.close_calls += 1


class _FakeAccessor:
    def __init__(
        self,
        records: list[tuple[int, int, str]],
        *,
        error: Exception | None = None,
    ) -> None:
        self.records: list[tuple[int, int, str]] = records
        self.error: Exception | None = error
        self.db: _FakeConnection = _FakeConnection()
        self.search_calls: list[tuple[str, bool, bool, bool]] = []

    def search(
        self,
        pattern: str,
        *,
        raw: bool,
        search_raw: bool,
        unique: bool,
    ) -> Iterator[tuple[int, int, str]]:
        self.search_calls.append((pattern, raw, search_raw, unique))
        yield from self.records
        if self.error is not None:
            raise self.error


def test_history_match_is_frozen_and_orders_only_by_location() -> None:
    first: HistoryMatch = HistoryMatch(1, 2, "z")
    same_location: HistoryMatch = HistoryMatch(1, 2, "a")
    later: HistoryMatch = HistoryMatch(2, 1, "a")

    assert first == same_location
    assert sorted([later, first]) == [first, later]
    with pytest.raises(FrozenInstanceError):
        first.source = "changed"  # type: ignore[misc]


def test_search_history_matches_across_sessions_in_location_order() -> None:
    records: list[tuple[int, int, str]] = [
        (3, 4, "print('needle')"),
        (1, 8, "needle = True"),
        (2, 1, "unrelated"),
        (1, 2, "# needle"),
    ]

    assert search_history("needle", records) == [
        HistoryMatch(1, 2, "# needle"),
        HistoryMatch(1, 8, "needle = True"),
        HistoryMatch(3, 4, "print('needle')"),
    ]


def test_search_history_returns_empty_list_when_nothing_matches() -> None:
    assert search_history("missing", [(1, 1, "value = 1")]) == []


def test_search_history_supports_multiline_source_and_regex_flags() -> None:
    source: str = "value = 1\nprint(value)\nvalue += 1"

    assert search_history(r"(?m)^print\(value\)$", [(2, 7, source)]) == [
        HistoryMatch(2, 7, source)
    ]


def test_search_history_propagates_invalid_regex() -> None:
    with pytest.raises(re.error):
        search_history("[", [(1, 1, "source")])


def test_search_history_consumes_one_shot_iterable_once() -> None:
    records: _OneShotHistory = _OneShotHistory([(2, 1, "target"), (1, 1, "target")])

    assert search_history("target", records) == [
        HistoryMatch(1, 1, "target"),
        HistoryMatch(2, 1, "target"),
    ]


def test_iter_ipython_history_uses_raw_unfiltered_nonunique_search() -> None:
    fake: _FakeAccessor = _FakeAccessor([(2, 3, "%time value")])

    assert list(iter_ipython_history(cast(HistoryAccessor, fake))) == [
        (2, 3, "%time value")
    ]
    assert fake.search_calls == [("*", True, True, False)]
    assert fake.db.close_calls == 0


def test_iter_ipython_history_does_not_close_injected_accessor_on_error() -> None:
    error: RuntimeError = RuntimeError("database read failed")
    fake: _FakeAccessor = _FakeAccessor([], error=error)

    with pytest.raises(RuntimeError, match="database read failed"):
        list(iter_ipython_history(cast(HistoryAccessor, fake)))

    assert fake.db.close_calls == 0


def test_iter_ipython_history_closes_internal_accessor_after_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake: _FakeAccessor = _FakeAccessor([(1, 1, "first")])

    monkeypatch.setattr(solution_00, "HistoryAccessor", lambda: fake)

    assert list(iter_ipython_history()) == [(1, 1, "first")]
    assert fake.db.close_calls == 1


def test_iter_ipython_history_closes_internal_accessor_when_generator_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake: _FakeAccessor = _FakeAccessor([(1, 1, "first"), (1, 2, "second")])
    generator: Generator[tuple[int, int, str], None, None]

    monkeypatch.setattr(solution_00, "HistoryAccessor", lambda: fake)
    generator = cast(
        Generator[tuple[int, int, str], None, None], iter_ipython_history()
    )

    assert next(generator) == (1, 1, "first")
    generator.close()
    assert fake.db.close_calls == 1


def test_iter_ipython_history_closes_internal_accessor_on_search_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    error: RuntimeError = RuntimeError("database read failed")
    fake: _FakeAccessor = _FakeAccessor([], error=error)

    monkeypatch.setattr(solution_00, "HistoryAccessor", lambda: fake)

    with pytest.raises(RuntimeError, match="database read failed"):
        list(iter_ipython_history())

    assert fake.db.close_calls == 1


def test_actual_history_accessor_reads_raw_inputs_from_explicit_temp_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    history_path: Path = tmp_path / "history.sqlite"

    def reject_profile_lookup(self: HistoryAccessor, profile: str) -> str:
        del self, profile
        raise AssertionError("user profile must not be consulted")

    monkeypatch.setattr(HistoryAccessor, "_get_hist_file_name", reject_profile_lookup)
    accessor_factory: Callable[..., HistoryAccessor] = cast(
        Callable[..., HistoryAccessor], HistoryAccessor
    )
    accessor: HistoryAccessor = accessor_factory(hist_file=str(history_path))
    connection: sqlite3.Connection = cast(
        sqlite3.Connection,
        accessor.db,  # pyright: ignore[reportUnknownMemberType]
    )
    try:
        connection.executemany(
            "INSERT INTO history(session, line, source, source_raw) VALUES (?, ?, ?, ?)",
            [
                (2, 4, "get_ipython().run_line_magic('time', 'value')", "%time value"),
                (1, 3, "print('translated')", "print('raw input')"),
            ],
        )
        connection.commit()

        assert set(iter_ipython_history(accessor)) == {
            (2, 4, "%time value"),
            (1, 3, "print('raw input')"),
        }
        assert history_path.is_file()
    finally:
        connection.close()


def test_main_prints_matches_and_returns_zero(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_history(
        accessor: HistoryAccessor | None = None,
    ) -> Iterator[tuple[int, int, str]]:
        assert accessor is None
        yield (2, 1, "nothing")
        yield (1, 4, "print('target')")

    monkeypatch.setattr(solution_00, "iter_ipython_history", fake_history)

    assert main(["target"]) == 0
    assert capsys.readouterr().out == "1:4: print('target')\n"


def test_main_prints_nothing_and_returns_one_when_no_match(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fake_history(
        accessor: HistoryAccessor | None = None,
    ) -> Iterator[tuple[int, int, str]]:
        assert accessor is None
        yield (1, 1, "nothing")

    monkeypatch.setattr(solution_00, "iter_ipython_history", fake_history)

    assert main(["target"]) == 1
    assert capsys.readouterr().out == ""


def test_main_propagates_invalid_regex(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_history(
        accessor: HistoryAccessor | None = None,
    ) -> Iterator[tuple[int, int, str]]:
        assert accessor is None
        raise AssertionError("history must not be read for an invalid regex")
        yield

    monkeypatch.setattr(solution_00, "iter_ipython_history", fake_history)

    with pytest.raises(re.error):
        main(["["])


def test_import_does_not_construct_accessor_or_emit_output() -> None:
    script: str = """
import IPython.core.history

def reject_construction(self, *args, **kwargs):
    raise AssertionError("HistoryAccessor constructed during import")

IPython.core.history.HistoryAccessor.__init__ = reject_construction
import CH_02_interactive_python.exercise_05.solution_00
"""
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""
