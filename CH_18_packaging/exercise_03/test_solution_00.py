"""Tests for safe static migration from legacy packaging metadata."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import zipfile
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from .solution_00 import (
    ProjectMetadata,
    migrate_project,
    read_setup_metadata,
    render_pyproject,
)

FIXTURE: Path = Path(__file__).with_name("fixtures") / "legacy_project"


def test_project_metadata_is_frozen() -> None:
    metadata: ProjectMetadata = ProjectMetadata(
        name="demo",
        version="1.2.3",
        description="Demo",
        requires_python=">=3.10",
        scripts={},
    )

    with pytest.raises(FrozenInstanceError):
        metadata.name = "changed"  # type: ignore[misc]


def test_read_setup_metadata_without_executing_setup(tmp_path: Path) -> None:
    marker: Path = tmp_path / "executed.txt"
    setup_py: Path = tmp_path / "setup.py"
    setup_py.write_text(
        "from pathlib import Path\n"
        "from setuptools import setup\n"
        f"Path({str(marker)!r}).write_text('executed')\n"
        "setup("
        "name='greeting-demo', "
        "version='1.2.3', "
        "description='A tiny migration fixture', "
        "python_requires='>=3.10', "
        "entry_points={'console_scripts': ['greet=greeting_demo:main']}"
        ")\n",
        encoding="utf-8",
    )

    metadata: ProjectMetadata = read_setup_metadata(setup_py)

    assert metadata == ProjectMetadata(
        name="greeting-demo",
        version="1.2.3",
        description="A tiny migration fixture",
        requires_python=">=3.10",
        scripts={"greet": "greeting_demo:main"},
    )
    assert not marker.exists()


def test_read_committed_fixture_metadata() -> None:
    assert read_setup_metadata(FIXTURE / "setup.py") == ProjectMetadata(
        name="greeting-demo",
        version="1.2.3",
        description="A tiny migration fixture",
        requires_python=">=3.10",
        scripts={"greet": "greeting_demo:main"},
    )


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (
            "from setuptools import setup\nsetup(name=get_name(), version='1.0.0')\n",
            "static literal",
        ),
        (
            "from setuptools import setup\n"
            "values = {'name': 'demo'}\n"
            "setup(**values)\n",
            "keyword expansion",
        ),
        (
            "from setuptools import setup\nsetup(name='one')\nsetup(name='two')\n",
            "exactly one setup",
        ),
        (
            "from setuptools import setup\n",
            "exactly one setup",
        ),
        (
            "from setuptools import setup\n"
            "setup(name='demo', version='1.0.0', description='Demo', "
            "python_requires='>=3.10', "
            "entry_points={'console_scripts': ['broken']})\n",
            "console script",
        ),
        (
            "from setuptools import setup\n"
            "setup(name='demo', version='1.0.0', description='Demo', "
            "python_requires='>=3.10', "
            "entry_points={'console_scripts': ["
            "'greet=demo:main', 'greet=demo:other']})\n",
            "duplicate console script",
        ),
        (
            "from setuptools import setup\n"
            "setup(name='demo', version='1.0.0', description='Demo', "
            "python_requires='>=3.10')\n",
            "required metadata",
        ),
        (
            "from setuptools import setup\nsetup(name='unterminated)\n",
            "valid Python",
        ),
    ],
)
def test_invalid_or_dynamic_setup_metadata_is_rejected(
    tmp_path: Path,
    content: str,
    message: str,
) -> None:
    setup_py: Path = tmp_path / "setup.py"
    setup_py.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match=message):
        read_setup_metadata(setup_py)


def test_render_pyproject_quotes_toml_strings_safely() -> None:
    metadata: ProjectMetadata = ProjectMetadata(
        name="quote-demo",
        version="1.2.3",
        description='A "quoted" description\non two lines',
        requires_python=">=3.10",
        scripts={"greet-tool": "greeting_demo:main"},
    )

    rendered: str = render_pyproject(metadata)

    assert 'requires = ["setuptools>=77", "wheel"]' in rendered
    assert "setuptools>=80" not in rendered
    assert 'description = "A \\"quoted\\" description\\non two lines"' in rendered
    assert '"greet-tool" = "greeting_demo:main"' in rendered


def _source_snapshot(source: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(source)): (
            b"SYMLINK\0" + os.fsencode(path.readlink())
            if path.is_symlink()
            else path.read_bytes()
        )
        for path in sorted(source.rglob("*"))
        if path.is_symlink() or path.is_file()
    }


def test_migrate_project_creates_deterministic_src_layout(tmp_path: Path) -> None:
    legacy_copy: Path = tmp_path / "legacy"
    shutil.copytree(FIXTURE, legacy_copy)
    before: dict[str, bytes] = _source_snapshot(legacy_copy)
    destination: Path = tmp_path / "migrated"

    migrated: Path = migrate_project(legacy_copy, destination)

    assert migrated == destination
    assert not (migrated / "setup.py").exists()
    assert (migrated / "README.rst").read_bytes() == (
        legacy_copy / "README.rst"
    ).read_bytes()
    assert (migrated / "src" / "greeting_demo" / "__init__.py").read_bytes() == (
        legacy_copy / "greeting_demo" / "__init__.py"
    ).read_bytes()
    assert _source_snapshot(legacy_copy) == before


def test_migrate_project_refuses_existing_destination(tmp_path: Path) -> None:
    destination: Path = tmp_path / "migrated"
    destination.mkdir()

    with pytest.raises(FileExistsError):
        migrate_project(FIXTURE, destination)


@pytest.mark.parametrize("distribution_name", [".", "../x", "a/b", r"a\b"])
def test_migrate_project_rejects_unsafe_distribution_names_before_copying(
    tmp_path: Path,
    distribution_name: str,
) -> None:
    source: Path = tmp_path / "legacy"
    source.mkdir()
    setup_py: Path = source / "setup.py"
    setup_py.write_text(
        "from setuptools import setup\n"
        f"setup(name={distribution_name!r}, version='1.2.3', "
        "description='Unsafe name fixture', python_requires='>=3.10', "
        "entry_points={'console_scripts': ['greet=greeting_demo:main']})\n",
        encoding="utf-8",
    )
    (source / "README.rst").write_text("Unsafe fixture\n==============\n")
    destination: Path = tmp_path / "migrated"
    original_setup: bytes = setup_py.read_bytes()

    with pytest.raises(ValueError, match="distribution name"):
        migrate_project(source, destination)

    assert setup_py.read_bytes() == original_setup
    assert not destination.exists()


def test_migrate_project_rejects_destination_inside_source_without_mutation(
    tmp_path: Path,
) -> None:
    source: Path = tmp_path / "legacy"
    shutil.copytree(FIXTURE, source)
    before: dict[str, bytes] = _source_snapshot(source)
    destination: Path = source / "migrated"

    with pytest.raises(ValueError, match="source and destination"):
        migrate_project(source, destination)

    assert _source_snapshot(source) == before
    assert not destination.exists()


@pytest.mark.parametrize("failure_point", ["copy2", "write"])
def test_migrate_project_failure_is_transactional(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_point: str,
) -> None:
    source: Path = tmp_path / "legacy"
    shutil.copytree(FIXTURE, source)
    before: dict[str, bytes] = _source_snapshot(source)
    destination: Path = tmp_path / "migrated"

    if failure_point == "copy2":

        def fail_copy2(source_path: Path, destination_path: Path) -> None:
            raise OSError("injected copy2 failure")

        monkeypatch.setattr(shutil, "copy2", fail_copy2)
    else:

        def fail_write_text(
            path: Path,
            data: str,
            encoding: str | None = None,
            errors: str | None = None,
            newline: str | None = None,
        ) -> int:
            raise OSError("injected write failure")

        monkeypatch.setattr(Path, "write_text", fail_write_text)

    with pytest.raises(OSError, match="injected"):
        migrate_project(source, destination)

    assert _source_snapshot(source) == before
    assert not destination.exists()
    assert list(tmp_path.glob(".migrated.tmp-*")) == []


def _assert_symlink_migration_rejected(
    source: Path,
    destination: Path,
    before: dict[str, bytes],
) -> None:
    with pytest.raises(ValueError, match="symlink"):
        migrate_project(source, destination)

    assert _source_snapshot(source) == before
    assert not destination.exists()
    assert list(destination.parent.glob(f".{destination.name}.tmp-*")) == []


def test_migrate_project_rejects_external_file_symlink(tmp_path: Path) -> None:
    source: Path = tmp_path / "legacy"
    shutil.copytree(FIXTURE, source)
    external_secret: Path = tmp_path / "secret.txt"
    external_secret.write_text("not package data\n", encoding="utf-8")
    (source / "greeting_demo" / "secret.txt").symlink_to(external_secret)
    before: dict[str, bytes] = _source_snapshot(source)

    _assert_symlink_migration_rejected(source, tmp_path / "migrated", before)


def test_migrate_project_rejects_directory_symlink(tmp_path: Path) -> None:
    source: Path = tmp_path / "legacy"
    shutil.copytree(FIXTURE, source)
    external_directory: Path = tmp_path / "external"
    external_directory.mkdir()
    (external_directory / "secret.txt").write_text("external\n", encoding="utf-8")
    (source / "greeting_demo" / "external").symlink_to(
        external_directory,
        target_is_directory=True,
    )
    before: dict[str, bytes] = _source_snapshot(source)

    _assert_symlink_migration_rejected(source, tmp_path / "migrated", before)


def test_migrate_project_rejects_symlink_package_root(tmp_path: Path) -> None:
    source: Path = tmp_path / "legacy"
    shutil.copytree(FIXTURE, source)
    package: Path = source / "greeting_demo"
    external_package: Path = tmp_path / "external_package"
    shutil.copytree(package, external_package)
    shutil.rmtree(package)
    package.symlink_to(external_package, target_is_directory=True)
    before: dict[str, bytes] = _source_snapshot(source)

    _assert_symlink_migration_rejected(source, tmp_path / "migrated", before)


def test_migrate_project_rejects_symlink_setup_py(tmp_path: Path) -> None:
    source: Path = tmp_path / "legacy"
    shutil.copytree(FIXTURE, source)
    setup_py: Path = source / "setup.py"
    external_setup: Path = tmp_path / "external_setup.py"
    shutil.copy2(setup_py, external_setup)
    setup_py.unlink()
    setup_py.symlink_to(external_setup)
    before: dict[str, bytes] = _source_snapshot(source)

    _assert_symlink_migration_rejected(source, tmp_path / "migrated", before)


@pytest.mark.timeout(90)
def test_migrated_project_builds_and_artifacts_are_usable(tmp_path: Path) -> None:
    legacy_copy: Path = tmp_path / "legacy"
    shutil.copytree(FIXTURE, legacy_copy)
    migrated: Path = migrate_project(legacy_copy, tmp_path / "migrated")
    dist: Path = tmp_path / "dist"

    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(dist),
            str(migrated),
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert completed.returncode == 0, completed.stderr
    wheels: list[Path] = list(dist.glob("*.whl"))
    sdists: list[Path] = list(dist.glob("*.tar.gz"))
    assert len(wheels) == 1
    assert len(sdists) == 1

    with zipfile.ZipFile(wheels[0]) as wheel:
        wheel_names: set[str] = set(wheel.namelist())
        assert "greeting_demo/__init__.py" in wheel_names
        metadata_name: str = next(
            name for name in wheel_names if name.endswith(".dist-info/METADATA")
        )
        entry_points_name: str = next(
            name for name in wheel_names if name.endswith(".dist-info/entry_points.txt")
        )
        metadata_text: str = wheel.read(metadata_name).decode("utf-8")
        entry_points_text: str = wheel.read(entry_points_name).decode("utf-8")
        assert "Name: greeting-demo" in metadata_text
        assert "Version: 1.2.3" in metadata_text
        assert "greet = greeting_demo:main" in entry_points_text

    with tarfile.open(sdists[0], mode="r:gz") as sdist:
        sdist_names: list[str] = sdist.getnames()
        assert any(name.endswith("/pyproject.toml") for name in sdist_names)
        assert any(
            name.endswith("/src/greeting_demo/__init__.py") for name in sdist_names
        )
        assert not any(name.endswith("/setup.py") for name in sdist_names)

    environment: dict[str, str] = os.environ.copy()
    environment["PYTHONPATH"] = str(wheels[0])
    smoke: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from greeting_demo import greeting, main; "
                "print(greeting('wheel')); main()"
            ),
        ],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )

    assert smoke.returncode == 0, smoke.stderr
    assert smoke.stdout.splitlines() == ["Hello, wheel!", "Hello, packaging!"]
