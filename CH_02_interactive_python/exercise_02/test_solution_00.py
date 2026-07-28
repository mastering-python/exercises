"""Tests for colored safe completions."""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable, Sequence

import pytest
from colorama import Fore, Style  # type: ignore[import-untyped]

from CH_02_interactive_python.exercise_01.solution_00 import Completer
from CH_02_interactive_python.exercise_02 import solution_00
from CH_02_interactive_python.exercise_02.solution_00 import (
    ColorCompleter,
    colorize,
)

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
_CompletionFunction = Callable[[str, int], str | None]
_DisplayHook = Callable[[str, Sequence[str], int], None]


class FakeReadline:
    def __init__(
        self,
        *,
        delimiters: str,
        library_version: str,
        backend: str | None = None,
    ) -> None:
        self.backend: str | None = backend
        self._READLINE_LIBRARY_VERSION: str = library_version
        self._delimiters: str = delimiters
        self.completer: _CompletionFunction | None = None
        self.display_hook: _DisplayHook | None = None
        self.bindings: list[str] = []
        self.redisplay_calls: int = 0

    def get_completer_delims(self) -> str:
        return self._delimiters

    def set_completer_delims(self, delimiters: str) -> None:
        self._delimiters = delimiters

    def set_completer(self, completer: _CompletionFunction | None = None) -> None:
        self.completer = completer

    def set_completion_display_matches_hook(
        self,
        hook: _DisplayHook | None = None,
    ) -> None:
        self.display_hook = hook

    def parse_and_bind(self, binding: str) -> None:
        self.bindings.append(binding)

    def redisplay(self) -> None:
        self.redisplay_calls += 1


def test_colorize_wraps_match_and_resets_style() -> None:
    assert colorize("candidate", Fore.RED) == (f"{Fore.RED}candidate{Style.RESET_ALL}")


def test_complete_returns_plain_first_sequence_candidate() -> None:
    completer: ColorCompleter = ColorCompleter({"values": ["alpha", "alpine"]})

    match: str | None = completer.complete("values[", 0)

    assert match == "values[0]"
    assert _ANSI_ESCAPE.search(match) is None


def test_complete_preserves_plain_candidates_and_sentinel() -> None:
    completer: ColorCompleter = ColorCompleter(
        {"values": {"alpha": 1, "alpine": 2}},
        color=Fore.MAGENTA,
    )

    matches: list[str | None] = [
        completer.complete("values[", state) for state in range(3)
    ]

    assert matches == [
        "values['alpha']",
        "values['alpine']",
        None,
    ]


def test_display_hook_colors_and_resets_each_candidate(
    capsys: pytest.CaptureFixture[str],
) -> None:
    completer: ColorCompleter = ColorCompleter(color=Fore.MAGENTA)

    completer.display_matches(
        "values[",
        ["values[0]", "values[1]"],
        len("values[0]"),
    )

    assert capsys.readouterr().out.splitlines() == [
        "",
        f"{Fore.MAGENTA}values[0]{Style.RESET_ALL}",
        f"{Fore.MAGENTA}values[1]{Style.RESET_ALL}",
    ]


def test_configure_gnu_readline_registers_hook_and_redisplays_buffer(
    capsys: pytest.CaptureFixture[str],
) -> None:
    readline: FakeReadline = FakeReadline(
        delimiters=" \t.[]'\"(),+-\\:",
        library_version="8.2",
    )
    completer: ColorCompleter = ColorCompleter({"values": [1]})

    solution_00.configure_readline(readline, completer)

    assert readline.get_completer_delims() == " \t:"
    assert readline.completer == completer.complete
    assert readline.display_hook is not None
    assert readline.bindings == ["tab: complete"]
    readline.display_hook("values[", ["values[0]"], len("values[0]"))
    assert capsys.readouterr().out.splitlines() == [
        "",
        f"{Fore.CYAN}values[0]{Style.RESET_ALL}",
    ]
    assert readline.redisplay_calls == 1


def test_configure_libedit_uses_plain_safe_fallback() -> None:
    readline: FakeReadline = FakeReadline(
        delimiters=" \t[]'\"",
        library_version="EditLine wrapper",
    )
    completer: ColorCompleter = ColorCompleter({"values": [1]})

    solution_00.configure_readline(readline, completer)

    assert readline.bindings == ["bind ^I rl_complete"]
    assert readline.display_hook is None
    assert readline.completer is not None
    assert readline.completer("values[", 0) == "values[0]"


def test_color_completer_inherits_safe_expression_rejection() -> None:
    calls: list[str] = []

    def dangerous() -> dict[str, int]:
        calls.append("called")
        return {"secret": 1}

    completer: ColorCompleter = ColorCompleter({"dangerous": dangerous})

    assert isinstance(completer, Completer)
    assert completer.complete("dangerous()[", 0) is None
    assert calls == []


def test_import_adds_no_terminal_or_readline_configuration() -> None:
    script = """
import importlib
import sys

import colorama
import readline
import CH_02_interactive_python.exercise_01.solution_00

def unexpected_call(*args: object, **kwargs: object) -> None:
    del args, kwargs
    raise AssertionError("import performed terminal setup")

colorama.just_fix_windows_console = unexpected_call
readline.set_completer = unexpected_call
readline.set_completer_delims = unexpected_call
readline.set_completion_display_matches_hook = unexpected_call
readline.parse_and_bind = unexpected_call

sys.modules.pop("CH_02_interactive_python.exercise_02.solution_00", None)
importlib.import_module("CH_02_interactive_python.exercise_02.solution_00")
"""

    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
