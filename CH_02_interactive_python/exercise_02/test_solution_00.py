"""Tests for colored safe completions."""

from __future__ import annotations

import re
import subprocess
import sys

from colorama import Fore, Style  # type: ignore[import-untyped]

from CH_02_interactive_python.exercise_01.solution_00 import Completer
from CH_02_interactive_python.exercise_02.solution_00 import (
    ColorCompleter,
    colorize,
)

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def test_colorize_wraps_match_and_resets_style() -> None:
    assert colorize("candidate", Fore.RED) == (f"{Fore.RED}candidate{Style.RESET_ALL}")


def test_default_color_preserves_first_candidate_text() -> None:
    completer: ColorCompleter = ColorCompleter({"values": {"alpha": 1, "alpine": 2}})

    match: str | None = completer.complete("values[", 0)

    assert match is not None
    assert match.startswith(Fore.CYAN)
    assert match.endswith(Style.RESET_ALL)
    assert _ANSI_ESCAPE.sub("", match) == "values['alpha']"


def test_custom_color_wraps_multiple_candidates_and_preserves_sentinel() -> None:
    completer: ColorCompleter = ColorCompleter(
        {"values": {"alpha": 1, "alpine": 2}},
        color=Fore.MAGENTA,
    )

    matches: list[str | None] = [
        completer.complete("values[", state) for state in range(3)
    ]

    assert matches == [
        f"{Fore.MAGENTA}values['alpha']{Style.RESET_ALL}",
        f"{Fore.MAGENTA}values['alpine']{Style.RESET_ALL}",
        None,
    ]


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
