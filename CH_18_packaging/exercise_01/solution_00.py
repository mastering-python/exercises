"""Strict semantic-version helpers and a setuptools bump command."""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar, Literal, cast

from setuptools import Command  # type: ignore[import-untyped]
from setuptools.errors import OptionError  # type: ignore[import-untyped]

VersionPart = Literal["major", "minor", "patch"]

VERSION_PATTERN: re.Pattern[str] = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"
)
ASSIGNMENT_PATTERN: re.Pattern[str] = re.compile(
    r"^(?P<prefix>[ \t]*__version__[ \t]*=[ \t]*)"
    r"(?P<quote>[\"'])(?P<version>[^\"'\r\n]+)(?P=quote)"
    r"(?P<suffix>[ \t]*(?:#[^\r\n]*)?\r?)$",
    re.MULTILINE,
)


def _validated_version(version: str) -> tuple[int, int, int]:
    match: re.Match[str] | None = VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise ValueError("version must use strict major.minor.patch integers")
    major: int
    minor: int
    patch: int
    major, minor, patch = (int(group) for group in match.groups())
    return major, minor, patch


def bump_version(version: str, part: VersionPart) -> str:
    """Increment one semantic-version part and reset lower-order parts."""

    major, minor, patch = _validated_version(version)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown version part: {part}")


def _find_version_assignment(content: str, path: Path) -> re.Match[str]:
    matches: list[re.Match[str]] = list(ASSIGNMENT_PATTERN.finditer(content))
    if len(matches) != 1:
        raise ValueError(f"{path} must contain exactly one __version__ assignment")
    return matches[0]


def read_version(path: Path) -> str:
    """Read one strict semantic version from a Python module."""

    content: str = path.read_bytes().decode("utf-8")
    match: re.Match[str] = _find_version_assignment(content, path)
    version: str = match.group("version")
    _validated_version(version)
    return version


def write_version(path: Path, version: str) -> None:
    """Replace only the version value while preserving all other module content."""

    _validated_version(version)
    content: str = path.read_bytes().decode("utf-8")
    match: re.Match[str] = _find_version_assignment(content, path)
    replacement: str = (
        f"{match.group('prefix')}{match.group('quote')}{version}"
        f"{match.group('quote')}{match.group('suffix')}"
    )
    updated: str = f"{content[: match.start()]}{replacement}{content[match.end() :]}"
    path.write_bytes(updated.encode("utf-8"))


class BumpVersion(Command):  # type: ignore[misc]
    """Setuptools command that bumps a designated Python version file."""

    description: str = "bump a package semantic version"
    user_options: ClassVar[
        list[tuple[str, str, str]] | list[tuple[str, str | None, str]]
    ] = cast(
        list[tuple[str, str | None, str]],
        [
            ("version-file=", None, "Python file containing __version__"),
            ("part=", None, "major, minor, or patch"),
        ],
    )

    version_file: str | None
    part: str | None

    def initialize_options(self) -> None:
        self.version_file = None
        self.part = "patch"

    def finalize_options(self) -> None:
        if self.version_file is None:
            raise OptionError("--version-file is required")
        if self.part not in {"major", "minor", "patch"}:
            raise OptionError("--part must be major, minor, or patch")

    def run(self) -> None:
        if self.version_file is None or self.part not in {
            "major",
            "minor",
            "patch",
        }:
            raise OptionError("command options were not finalized")
        path: Path = Path(self.version_file)
        current: str = read_version(path)
        part: VersionPart = cast(VersionPart, self.part)
        updated: str = bump_version(current, part)
        write_version(path, updated)
        self.announce(f"bumped {current} to {updated}", level=2)
