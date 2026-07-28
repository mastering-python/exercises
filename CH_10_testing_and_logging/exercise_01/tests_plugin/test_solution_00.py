"""Exercise the documentation plugin through real pytest collection."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PLUGIN: str = "CH_10_testing_and_logging.exercise_01.file_documentation_plugin"
REPOSITORY_ROOT: Path = Path(__file__).parents[3]


def _run_collection(directory: Path) -> subprocess.CompletedProcess[str]:
    environment: dict[str, str] = os.environ.copy()
    existing_path: str = environment.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(REPOSITORY_ROOT), existing_path) if part
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            PLUGIN,
            "--collect-only",
            "-q",
        ],
        cwd=directory,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


def _configure(directory: Path) -> None:
    (directory / "pytest.ini").write_text(
        "[pytest]\npython_files = check_*.py\n",
        encoding="utf-8",
    )


def test_collects_documented_python_test_matching_configured_pattern(
    tmp_path: Path,
) -> None:
    _configure(tmp_path)
    (tmp_path / "check_documented.py").write_text(
        '"""File-level documentation."""\n\n'
        "def test_example() -> None:\n"
        "    assert True\n",
        encoding="utf-8",
    )

    completed: subprocess.CompletedProcess[str] = _run_collection(tmp_path)

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "1 test collected" in completed.stdout


def test_rejects_matching_python_test_without_module_docstring(
    tmp_path: Path,
) -> None:
    _configure(tmp_path)
    (tmp_path / "check_undocumented.py").write_text(
        "def test_example() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    completed: subprocess.CompletedProcess[str] = _run_collection(tmp_path)
    output: str = completed.stdout + completed.stderr

    assert completed.returncode == 2
    assert "Python test module requires a file-level docstring" in output
    assert "check_undocumented.py" in output


def test_rejects_malformed_matching_python_test_with_clear_error(
    tmp_path: Path,
) -> None:
    _configure(tmp_path)
    (tmp_path / "check_malformed.py").write_text(
        "def test_broken(:\n",
        encoding="utf-8",
    )

    completed: subprocess.CompletedProcess[str] = _run_collection(tmp_path)
    output: str = completed.stdout + completed.stderr

    assert completed.returncode == 2
    assert "Malformed Python test module" in output
    assert "check_malformed.py:1" in output


def test_does_not_claim_non_test_python_files(tmp_path: Path) -> None:
    _configure(tmp_path)
    (tmp_path / "check_documented.py").write_text(
        '"""File-level documentation."""\n\n'
        "def test_example() -> None:\n"
        "    assert True\n",
        encoding="utf-8",
    )
    (tmp_path / "application.py").write_text(
        "def malformed(:\n",
        encoding="utf-8",
    )

    completed: subprocess.CompletedProcess[str] = _run_collection(tmp_path)
    output: str = completed.stdout + completed.stderr

    assert completed.returncode == 0, output
    assert "1 test collected" in completed.stdout
    assert "application.py" not in output


def test_path_patterns_apply_to_nested_python_test_files(tmp_path: Path) -> None:
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\npython_files = nested/check_*.py\n",
        encoding="utf-8",
    )
    nested: Path = tmp_path / "nested"
    nested.mkdir()
    (nested / "check_undocumented.py").write_text(
        "def test_example() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    completed: subprocess.CompletedProcess[str] = _run_collection(tmp_path)
    output: str = completed.stdout + completed.stderr

    assert completed.returncode == 2
    assert "Python test module requires a file-level docstring" in output
    assert "check_undocumented.py" in output
