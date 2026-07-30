"""Tests for the non-interactive setuptools version-bump command."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .solution_00 import VersionPart, bump_version, read_version, write_version


@pytest.mark.parametrize(
    ("part", "expected"),
    [
        ("major", "2.0.0"),
        ("minor", "1.3.0"),
        ("patch", "1.2.4"),
    ],
)
def test_bump_version_parts(part: VersionPart, expected: str) -> None:
    assert bump_version("1.2.3", part) == expected


@pytest.mark.parametrize(
    "version",
    ["1.2", "1.2.x", "v1.2.3", "1.-2.3", "01.2.3", "1.02.3", "1.2.03"],
)
def test_bump_version_rejects_invalid_versions(version: str) -> None:
    with pytest.raises(ValueError, match=r"major\.minor\.patch"):
        bump_version(version, "patch")


def test_bump_version_rejects_unknown_part() -> None:
    with pytest.raises(ValueError, match="unknown version part"):
        bump_version("1.2.3", "fourth")  # type: ignore[arg-type]


def test_read_and_write_version_preserve_module_content(tmp_path: Path) -> None:
    version_file: Path = tmp_path / "__init__.py"
    version_file.write_text(
        'NAME = "demo"\n__version__ = "1.2.3"\nENABLED = True\n',
        encoding="utf-8",
    )

    assert read_version(version_file) == "1.2.3"
    write_version(version_file, "1.2.4")

    assert version_file.read_text(encoding="utf-8") == (
        'NAME = "demo"\n__version__ = "1.2.4"\nENABLED = True\n'
    )


def test_read_and_write_version_preserve_crlf_and_mixed_file_bytes(
    tmp_path: Path,
) -> None:
    version_file: Path = tmp_path / "__init__.py"
    original: bytes = (
        b'NAME = "demo"\r\n'
        b'__version__ = "1.2.3"\r\n'
        b"UNIX_LINE = True\n"
        b'PAYLOAD = "\\r\\n"\r\n'
    )
    version_file.write_bytes(original)

    assert read_version(version_file) == "1.2.3"
    write_version(version_file, "1.2.4")

    assert version_file.read_bytes() == original.replace(b"1.2.3", b"1.2.4")


@pytest.mark.parametrize(
    "content",
    [
        'NAME = "demo"\n',
        '__version__ = "1.2.3"\n__version__ = "1.2.4"\n',
    ],
)
def test_read_version_requires_exactly_one_assignment(
    tmp_path: Path,
    content: str,
) -> None:
    version_file: Path = tmp_path / "__init__.py"
    version_file.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="exactly one __version__ assignment"):
        read_version(version_file)


def test_write_version_rejects_invalid_new_version(tmp_path: Path) -> None:
    version_file: Path = tmp_path / "__init__.py"
    version_file.write_text('__version__ = "1.2.3"\n', encoding="utf-8")

    with pytest.raises(ValueError, match=r"major\.minor\.patch"):
        write_version(version_file, "1.2")

    assert version_file.read_text(encoding="utf-8") == '__version__ = "1.2.3"\n'


def _write_command_fixture(tmp_path: Path) -> tuple[Path, Path]:
    package: Path = tmp_path / "demo_package"
    package.mkdir()
    version_file: Path = package / "__init__.py"
    version_file.write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    untouched_file: Path = package / "metadata.py"
    untouched_file.write_text('__version__ = "9.9.9"\n', encoding="utf-8")
    shutil.copy(
        Path(__file__).with_name("solution_00.py"),
        tmp_path / "bump_command.py",
    )
    (tmp_path / "setup.py").write_text(
        "from setuptools import setup\n"
        "from bump_command import BumpVersion\n"
        "setup(name='demo-package', version='1.2.3', "
        "cmdclass={'bump_version': BumpVersion})\n",
        encoding="utf-8",
    )
    return version_file, untouched_file


def _run_bump_command(
    tmp_path: Path,
    *options: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "setup.py", "bump_version", *options],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )


@pytest.mark.timeout(30)
def test_setuptools_command_defaults_to_patch_and_only_writes_designated_file(
    tmp_path: Path,
) -> None:
    version_file, untouched_file = _write_command_fixture(tmp_path)

    completed: subprocess.CompletedProcess[str] = _run_bump_command(
        tmp_path,
        "--version-file",
        "demo_package/__init__.py",
    )

    assert completed.returncode == 0, completed.stderr
    assert read_version(version_file) == "1.2.4"
    assert read_version(untouched_file) == "9.9.9"


@pytest.mark.timeout(30)
def test_setuptools_command_accepts_explicit_part(tmp_path: Path) -> None:
    version_file, _ = _write_command_fixture(tmp_path)

    completed: subprocess.CompletedProcess[str] = _run_bump_command(
        tmp_path,
        "--version-file",
        "demo_package/__init__.py",
        "--part",
        "minor",
    )

    assert completed.returncode == 0, completed.stderr
    assert read_version(version_file) == "1.3.0"


@pytest.mark.timeout(30)
def test_setuptools_command_validates_required_options(tmp_path: Path) -> None:
    _write_command_fixture(tmp_path)

    completed: subprocess.CompletedProcess[str] = _run_bump_command(tmp_path)

    assert completed.returncode != 0
    assert "--version-file is required" in completed.stderr
