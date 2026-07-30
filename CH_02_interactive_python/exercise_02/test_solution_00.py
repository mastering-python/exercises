"""Tests for colored safe completions."""

from __future__ import annotations

import importlib.util
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
        line_buffer: str = "",
    ) -> None:
        self.backend: str | None = backend
        self._READLINE_LIBRARY_VERSION: str = library_version
        self._delimiters: str = delimiters
        self.completer: _CompletionFunction | None = None
        self.display_hook: _DisplayHook | None = None
        self.bindings: list[str] = []
        self.line_buffer: str = line_buffer

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

    def get_line_buffer(self) -> str:
        return self.line_buffer


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


def test_configure_gnu_readline_restores_prompt_and_current_buffer(
    capsys: pytest.CaptureFixture[str],
) -> None:
    readline: FakeReadline = FakeReadline(
        delimiters=" \t.[]'\"(),+-\\:",
        library_version="8.2",
        line_buffer="config['",
    )
    completer: ColorCompleter = ColorCompleter({"values": [1]})

    solution_00.configure_readline(readline, completer, prompt=">>> ")

    assert readline.get_completer_delims() == " \t:"
    assert readline.completer == completer.complete
    assert readline.display_hook is not None
    assert readline.bindings == ["tab: complete"]
    readline.display_hook("values[", ["values[0]"], len("values[0]"))
    output: str = capsys.readouterr().out
    assert output.startswith(f"\n{Fore.CYAN}values[0]{Style.RESET_ALL}\n")
    assert output.endswith(">>> config['")


def test_configure_libedit_uses_plain_safe_fallback() -> None:
    readline: FakeReadline = FakeReadline(
        delimiters=" \t[]'\"",
        library_version="EditLine wrapper",
    )
    completer: ColorCompleter = ColorCompleter({"values": [1]})

    solution_00.configure_readline(readline, completer, prompt=">>> ")

    assert readline.bindings == ["bind ^I rl_complete"]
    assert readline.display_hook is None
    assert readline.completer is not None
    assert readline.completer("values[", 0) == "values[0]"


@pytest.mark.integration
def test_gnu_readline_pty_restores_prompt_and_plain_buffer() -> None:
    if (
        importlib.util.find_spec("gnureadline") is None
        or importlib.util.find_spec("pexpect") is None
    ):
        pytest.skip("requires the optional gnureadline and pexpect packages")

    script: str = r'''
import io
import sys

import pexpect

child_code = """
import sys
import gnureadline as readline
sys.modules["readline"] = readline
from CH_02_interactive_python.exercise_02.solution_00 import (
    ColorCompleter,
    PROMPT,
    configure_readline,
)

completer = ColorCompleter({"config": {"host": "localhost", "port": 8000}})
configure_readline(readline, completer, prompt=PROMPT)
value = input(PROMPT)
print("FINAL=" + value)
"""
transcript_stream = io.StringIO()
child = pexpect.spawn(
    sys.executable,
    ["-c", child_code],
    encoding="utf-8",
    timeout=10,
)
child.logfile_read = transcript_stream
child.expect_exact(">>> ")
child.send("config[\x27")
child.send("\t\t")
child.expect_exact("\x1b[36mconfig[\x27host\x27]\x1b[0m")
child.expect_exact(">>> config[\x27")
child.send("h\r")
child.expect_exact("FINAL=config[\x27h")
child.expect(pexpect.EOF)
transcript = transcript_stream.getvalue()
assert ">>> config[\x27h" in transcript
final_text = transcript.rsplit("FINAL=", 1)[1]
assert "\x1b[" not in final_text
print(repr(transcript))
'''
    result: subprocess.CompletedProcess[str] = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "FINAL=config['h" in result.stdout


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
