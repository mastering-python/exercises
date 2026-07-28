"""Tests for the Jedi-based source completer."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol, cast

import jedi  # type: ignore[import-untyped]
import pytest

from CH_02_interactive_python.exercise_03.solution_00 import complete_source


class _JediCompletion(Protocol):
    @property
    def name_with_symbols(self) -> str: ...


class _JediScript(Protocol):
    def complete(self, line: int, column: int) -> Iterable[_JediCompletion]: ...


def _direct_jedi_names(source: str, *, line: int, column: int) -> list[str]:
    script: _JediScript = cast(_JediScript, jedi.Script(code=source))
    completions: Iterable[_JediCompletion] = script.complete(line, column)
    return sorted(
        {completion.name_with_symbols for completion in completions},
    )


def test_pathlib_incomplete_import_includes_path() -> None:
    source: str = "from pathlib import Pa"

    assert "Path" in complete_source(source)


def test_explicit_coordinates_complete_middle_of_source() -> None:
    target_line: str = "from pathlib import Pa"
    source: str = f"{target_line}\nunrelated_name = 1"

    completions: list[str] = complete_source(
        source,
        line=1,
        column=len(target_line),
    )

    assert "Path" in completions


class _FakeCompletion:
    def __init__(self, name_with_symbols: str) -> None:
        self.name_with_symbols: str = name_with_symbols


class _FakeScript:
    def __init__(self, *, code: str) -> None:
        assert code == "candidate"

    def complete(self, line: int, column: int) -> list[_FakeCompletion]:
        assert (line, column) == (1, len("candidate"))
        return [
            _FakeCompletion("zeta"),
            _FakeCompletion("alpha"),
            _FakeCompletion("zeta"),
        ]


def test_returns_sorted_unique_candidate_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "CH_02_interactive_python.exercise_03.solution_00.jedi.Script",
        _FakeScript,
    )

    assert complete_source("candidate") == ["alpha", "zeta"]


def test_empty_source_uses_first_line_at_column_zero() -> None:
    completions: list[str] = complete_source("")

    assert "abs" in completions
    assert completions == sorted(set(completions))


def test_default_targets_terminal_empty_line() -> None:
    source: str = "x\n"
    expected: list[str] = _direct_jedi_names(source, line=2, column=0)

    assert complete_source(source) == expected


def test_explicit_terminal_empty_line_coordinate_is_valid() -> None:
    source: str = "x\n"

    assert complete_source(source, line=2, column=0) == _direct_jedi_names(
        source,
        line=2,
        column=0,
    )


@pytest.mark.parametrize(
    ("source", "final_line"),
    [
        ("x\n\n", 3),
        ("x\r\n\r\n", 3),
    ],
)
def test_default_targets_final_line_after_multiple_newlines(
    source: str,
    final_line: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, int, int]] = []

    class RecordingScript:
        def __init__(self, *, code: str) -> None:
            self.source: str = code

        def complete(self, line: int, column: int) -> list[_FakeCompletion]:
            calls.append((self.source, line, column))
            return []

    monkeypatch.setattr(
        "CH_02_interactive_python.exercise_03.solution_00.jedi.Script",
        RecordingScript,
    )

    assert complete_source(source) == []
    assert calls == [(source, final_line, 0)]


@pytest.mark.parametrize(
    ("source", "line", "column", "message"),
    [
        ("value", 0, 0, "line"),
        ("value", 2, 0, "line"),
        ("value", 1, -1, "column"),
        ("value", 1, len("value") + 1, "column"),
    ],
)
def test_rejects_invalid_coordinates(
    source: str,
    line: int,
    column: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        complete_source(source, line=line, column=column)


def test_source_runtime_calls_are_not_executed(tmp_path: Path) -> None:
    marker: Path = tmp_path / "marker.txt"
    marker.write_text("unchanged")
    source: str = (
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('changed')\nPath."
    )

    # This checks direct source evaluation, not whether Jedi is a security sandbox.
    complete_source(source)

    assert marker.read_text() == "unchanged"


def test_import_has_no_output_or_demo_side_effects() -> None:
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_02_interactive_python.exercise_03.solution_00",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout == ""
    assert result.stderr == ""
