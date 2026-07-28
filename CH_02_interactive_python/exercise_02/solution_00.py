"""Color safe completion candidates."""

from __future__ import annotations

from collections.abc import Mapping

import colorama  # type: ignore[import-untyped]
from colorama import Fore, Style

from CH_02_interactive_python.exercise_01.solution_00 import Completer


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
        """Return the requested colored candidate or the completion sentinel."""
        match: str | None = super().complete(text, state)
        if match is None:
            return None
        return colorize(match, self._color)


def main() -> None:
    """Run an interactive colored-completion demonstration."""
    import readline

    colorama.just_fix_windows_console()
    completer: ColorCompleter = ColorCompleter(
        {"config": {"host": "localhost", "port": 8000}}
    )
    readline.set_completer(completer.complete)
    readline.parse_and_bind("tab: complete")
    try:
        input("Type config[ and press Tab: ")
    except EOFError:
        pass


if __name__ == "__main__":
    main()
