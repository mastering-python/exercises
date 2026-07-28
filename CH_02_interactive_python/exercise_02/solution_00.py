"""Color safe completion candidates."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Final, Protocol

from colorama import (  # type: ignore[import-untyped]
    Fore,
    Style,
    just_fix_windows_console,
)

from CH_02_interactive_python.exercise_01.solution_00 import Completer

_CompletionFunction = Callable[[str, int], str | None]
_DisplayHook = Callable[[str, Sequence[str], int], None]
_EXPRESSION_CHARACTERS: Final[frozenset[str]] = frozenset(".[]'\"(),+-\\")
PROMPT: Final[str] = ">>> "


class ReadlineLike(Protocol):
    """Readline operations needed by the interactive demonstration."""

    def get_completer_delims(self) -> str: ...

    def set_completer_delims(self, delimiters: str, /) -> None: ...

    def set_completer(
        self,
        completer: _CompletionFunction | None = None,
        /,
    ) -> None: ...

    def set_completion_display_matches_hook(
        self,
        hook: _DisplayHook | None = None,
        /,
    ) -> None: ...

    def parse_and_bind(self, binding: str, /) -> None: ...

    def get_line_buffer(self) -> str: ...


def colorize(match: str, color: str) -> str:
    """Wrap a completion candidate in a color and reset the terminal style."""
    return f"{color}{match}{Style.RESET_ALL}"


class ColorCompleter(Completer):
    """Color candidates produced by the safe completer."""

    def __init__(
        self,
        namespace: Mapping[str, object] | None = None,
        *,
        color: str = Fore.CYAN,
    ) -> None:
        super().__init__(namespace)
        self._color: str = color

    def complete(self, text: str, state: int) -> str | None:
        """Return the requested plain candidate or the completion sentinel."""
        return super().complete(text, state)

    def display_matches(
        self,
        substitution: str,
        matches: Sequence[str],
        longest_match_length: int,
    ) -> None:
        """Display colored candidates without changing replacement text."""
        del substitution, longest_match_length
        print()
        match: str
        for match in matches:
            print(colorize(match, self._color))


def _completion_delimiters(delimiters: str) -> str:
    kept: list[str] = []
    character: str
    for character in delimiters:
        if character not in _EXPRESSION_CHARACTERS:
            kept.append(character)
    return "".join(kept)


def _uses_libedit(readline_module: ReadlineLike) -> bool:
    backend: object = getattr(readline_module, "backend", None)
    if backend == "editline":
        return True
    if backend == "readline":
        return False

    library_version: object = getattr(
        readline_module,
        "_READLINE_LIBRARY_VERSION",
        "",
    )
    if isinstance(library_version, str) and "editline" in library_version.casefold():
        return True

    documentation: object = getattr(readline_module, "__doc__", "")
    return isinstance(documentation, str) and "libedit" in documentation.casefold()


def _display_hook(
    readline_module: ReadlineLike,
    completer: ColorCompleter,
    prompt: str,
) -> _DisplayHook:
    def display_matches(
        substitution: str,
        matches: Sequence[str],
        longest_match_length: int,
    ) -> None:
        completer.display_matches(substitution, matches, longest_match_length)
        restored_line: str = f"{prompt}{readline_module.get_line_buffer()}"
        print(restored_line, end="", flush=True)

    return display_matches


def configure_readline(
    readline_module: ReadlineLike,
    completer: ColorCompleter,
    *,
    prompt: str,
) -> None:
    """Configure safe expression completion for GNU readline or libedit."""
    delimiters: str = _completion_delimiters(readline_module.get_completer_delims())
    readline_module.set_completer_delims(delimiters)
    readline_module.set_completer(completer.complete)
    uses_libedit: bool = _uses_libedit(readline_module)
    if not uses_libedit:
        readline_module.set_completion_display_matches_hook(
            _display_hook(readline_module, completer, prompt)
        )
    binding: str = "bind ^I rl_complete" if uses_libedit else "tab: complete"
    readline_module.parse_and_bind(binding)


def main() -> None:
    """Run an interactive completion demonstration."""
    import readline

    just_fix_windows_console()
    completer: ColorCompleter = ColorCompleter(
        {"config": {"host": "localhost", "port": 8000}}
    )
    configure_readline(readline, completer, prompt=PROMPT)
    try:
        input(PROMPT)
    except EOFError:
        pass


if __name__ == "__main__":
    main()
