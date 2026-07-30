"""Tests for the interactive setuptools version-bump command."""

from __future__ import annotations

import builtins
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from setuptools import Distribution  # type: ignore[import-untyped]

from CH_18_packaging.exercise_01.solution_00 import read_version

from .solution_00 import InteractiveBumpVersion, choose_version_part


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("major", "major"),
        ("2", "minor"),
        ("PATCH", "patch"),
        (" 1 ", "major"),
        ("Minor", "minor"),
        ("3", "patch"),
    ],
)
def test_choose_version_part_accepts_names_and_numbers(
    answer: str,
    expected: str,
) -> None:
    responses: Iterator[str] = iter([answer])

    assert choose_version_part(lambda prompt: next(responses)) == expected


def test_choose_version_part_rejects_invalid_choice() -> None:
    with pytest.raises(ValueError, match="major, minor, or patch"):
        choose_version_part(lambda prompt: "fourth")


def _write_interactive_fixture(tmp_path: Path) -> Path:
    package: Path = tmp_path / "demo_package"
    package.mkdir()
    version_file: Path = package / "__init__.py"
    version_file.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    shutil.copy(
        Path(__file__).with_name("solution_00.py"),
        tmp_path / "interactive_bump.py",
    )
    (tmp_path / "setup.py").write_text(
        "from setuptools import setup\n"
        "from interactive_bump import InteractiveBumpVersion\n"
        "setup(name='demo-package', version='1.2.3', "
        "cmdclass={'bump_version': InteractiveBumpVersion})\n",
        encoding="utf-8",
    )
    return version_file


@pytest.mark.timeout(30)
def test_interactive_command_uses_stdin(tmp_path: Path) -> None:
    version_file: Path = _write_interactive_fixture(tmp_path)
    environment: dict[str, str] = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).parents[2])

    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "setup.py",
            "bump_version",
            "--version-file",
            "demo_package/__init__.py",
        ],
        cwd=tmp_path,
        env=environment,
        input="minor\n",
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert completed.returncode == 0, completed.stderr
    assert read_version(version_file) == "1.3.0"


def test_explicit_part_bypasses_input(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version_file: Path = tmp_path / "__init__.py"
    version_file.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    command: InteractiveBumpVersion = InteractiveBumpVersion(Distribution())
    command.version_file = str(version_file)
    command.part = "major"

    def fail_input(prompt: str) -> str:
        raise AssertionError(f"unexpected prompt: {prompt}")

    monkeypatch.setattr(builtins, "input", fail_input)
    command.finalize_options()
    command.run()

    assert read_version(version_file) == "2.0.0"


def test_direct_command_prompts_when_part_is_not_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    version_file: Path = tmp_path / "__init__.py"
    version_file.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    command: InteractiveBumpVersion = InteractiveBumpVersion(Distribution())
    command.version_file = str(version_file)

    def choose_patch(prompt: str) -> str:
        return "patch"

    monkeypatch.setattr(builtins, "input", choose_patch)

    command.finalize_options()
    command.run()

    assert read_version(version_file) == "1.2.4"
