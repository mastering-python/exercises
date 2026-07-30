"""Interactive extension of the setuptools version-bump command."""

from __future__ import annotations

import builtins
from collections.abc import Callable

from CH_18_packaging.exercise_01.solution_00 import BumpVersion, VersionPart

CHOICES: dict[str, VersionPart] = {
    "1": "major",
    "major": "major",
    "2": "minor",
    "minor": "minor",
    "3": "patch",
    "patch": "patch",
}


def choose_version_part(
    input_function: Callable[[str], str] | None = None,
) -> VersionPart:
    """Read and validate a numeric or named semantic-version part."""

    reader: Callable[[str], str] = (
        builtins.input if input_function is None else input_function
    )
    answer: str = reader("Choose version bump: 1) major, 2) minor, 3) patch: ").strip()
    try:
        return CHOICES[answer.lower()]
    except KeyError as error:
        raise ValueError("choose major, minor, or patch") from error


class InteractiveBumpVersion(BumpVersion):
    """Setuptools command that prompts unless ``--part`` is supplied."""

    description: str = "interactively choose a package semantic-version bump"

    def initialize_options(self) -> None:
        super().initialize_options()
        self.part = "interactive"

    def finalize_options(self) -> None:
        if self.part is None or self.part == "interactive":
            self.part = choose_version_part()
        super().finalize_options()
