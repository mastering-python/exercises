# Chapter 18 Packaging Implementation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a setuptools version-bump command, an interactive major/minor/patch extension, and a tested migration from a static `setup.py` project to modern `pyproject.toml`.

**Architecture:** Exercises 1 and 2 expose reusable version parsing/bumping functions plus setuptools `Command` subclasses that tests install into temporary fixture projects. Exercise 3 parses a deliberately static legacy fixture without executing it, migrates to a `src` layout, builds wheel and sdist in a temporary directory, and verifies artifact contents.

**Tech Stack:** Python 3.10, setuptools, wheel, `build`, tox, pytest, subprocess, zipfile, tarfile, uv.

---

## Coordinator dependency handoff

Do not modify shared project files. Confirm the coordinator's `packaging` group includes setuptools, build, wheel, and tox. Every subprocess must use `sys.executable`, set `cwd` to a temporary fixture, disable network-dependent isolation where required, capture stdout/stderr, and use a timeout.

## File map

- Create complete exercise directories `exercise_01/`, `exercise_02/`, and `exercise_03/`.
- Exercise 3 adds only `fixtures/legacy_project/setup.py`, `README.rst`, and `greeting_demo/__init__.py`.
- Modify `CH_18_packaging/README.rst` only to link the three exact questions.

### Task 1: Non-interactive setuptools bump command

**Files:**
- Create: `CH_18_packaging/exercise_01/__init__.py`
- Create: `CH_18_packaging/exercise_01/solution_00.py`
- Create: `CH_18_packaging/exercise_01/test_solution_00.py`

- [ ] **Step 1: Write failing version and command-integration tests**

```python
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .solution_00 import bump_version, read_version, write_version


def test_bump_version_parts() -> None:
    assert bump_version("1.2.3", "major") == "2.0.0"
    assert bump_version("1.2.3", "minor") == "1.3.0"
    assert bump_version("1.2.3", "patch") == "1.2.4"


@pytest.mark.parametrize("version", ["1.2", "1.2.x", "v1.2.3", "1.-2.3"])
def test_bump_version_rejects_invalid_versions(version: str) -> None:
    with pytest.raises(ValueError, match="major.minor.patch"):
        bump_version(version, "patch")


def test_read_and_write_version_preserve_module_content(tmp_path: Path) -> None:
    version_file: Path = tmp_path / "__init__.py"
    version_file.write_text('NAME = "demo"\n__version__ = "1.2.3"\n', encoding="utf-8")
    assert read_version(version_file) == "1.2.3"
    write_version(version_file, "1.2.4")
    assert version_file.read_text(encoding="utf-8") == (
        'NAME = "demo"\n__version__ = "1.2.4"\n'
    )


@pytest.mark.timeout(30)
def test_setuptools_command_bumps_fixture_patch(tmp_path: Path) -> None:
    package: Path = tmp_path / "demo_package"
    package.mkdir()
    (package / "__init__.py").write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    shutil.copy(Path(__file__).with_name("solution_00.py"), tmp_path / "bump_command.py")
    (tmp_path / "setup.py").write_text(
        "from setuptools import setup\n"
        "from bump_command import BumpVersion\n"
        "setup(name='demo-package', version='1.2.3', "
        "cmdclass={'bump_version': BumpVersion})\n",
        encoding="utf-8",
    )
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "setup.py",
            "bump_version",
            "--version-file",
            "demo_package/__init__.py",
            "--part",
            "patch",
        ],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    assert read_version(package / "__init__.py") == "1.2.4"
```

- [ ] **Step 2: Run tests and verify the exercise is absent**

Run `uv run --group packaging pytest CH_18_packaging/exercise_01/test_solution_00.py -vv`.

Expected: FAIL during import.

- [ ] **Step 3: Implement strict semantic-version helpers**

```python
from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, cast


VersionPart = Literal["major", "minor", "patch"]
VERSION_PATTERN: re.Pattern[str] = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
ASSIGNMENT_PATTERN: re.Pattern[str] = re.compile(
    r'^(?P<prefix>__version__\s*=\s*["\'])(?P<version>[^"\']+)(?P<suffix>["\']\s*)$',
    re.MULTILINE,
)


def bump_version(version: str, part: VersionPart) -> str:
    match: re.Match[str] | None = VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise ValueError("version must be major.minor.patch")
    major: int
    minor: int
    patch: int
    major, minor, patch = (int(group) for group in match.groups())
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"unknown version part: {part}")


def read_version(path: Path) -> str:
    content: str = path.read_text(encoding="utf-8")
    match: re.Match[str] | None = ASSIGNMENT_PATTERN.search(content)
    if match is None:
        raise ValueError(f"{path} must contain one __version__ assignment")
    version: str = match.group("version")
    if VERSION_PATTERN.fullmatch(version) is None:
        raise ValueError("version must be major.minor.patch")
    return version


def write_version(path: Path, version: str) -> None:
    if VERSION_PATTERN.fullmatch(version) is None:
        raise ValueError("version must be major.minor.patch")
    content: str = path.read_text(encoding="utf-8")
    updated: str
    replacements: int
    updated, replacements = ASSIGNMENT_PATTERN.subn(
        lambda match: f"{match.group('prefix')}{version}{match.group('suffix')}",
        content,
        count=1,
    )
    if replacements != 1:
        raise ValueError(f"{path} must contain one __version__ assignment")
    path.write_text(updated, encoding="utf-8")
```

- [ ] **Step 4: Implement the setuptools command**

```python
from setuptools import Command, Distribution
from setuptools.errors import OptionError


class BumpVersion(Command):
    description: str = "bump a package version"
    user_options: list[tuple[str, str | None, str]] = [
        ("version-file=", None, "Python file containing __version__"),
        ("part=", None, "major, minor, or patch"),
    ]

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
        if self.version_file is None or self.part not in {"major", "minor", "patch"}:
            raise OptionError("command options were not finalized")
        path: Path = Path(self.version_file)
        current: str = read_version(path)
        part: VersionPart = cast(VersionPart, self.part)
        new: str = bump_version(current, part)
        write_version(path, new)
        self.announce(f"bumped {current} to {new}", level=2)
```

Remove unused `Distribution` if the installed setuptools annotations do not require it. Do not edit `setup.py` metadata; the exercise command changes only the designated package version file.

- [ ] **Step 5: Verify and commit**

```bash
uv run --group packaging pytest CH_18_packaging/exercise_01/test_solution_00.py -vv
uv run ruff format --check CH_18_packaging/exercise_01
uv run ruff check CH_18_packaging/exercise_01
uv run pyrefly check CH_18_packaging/exercise_01
uv run mypy CH_18_packaging/exercise_01
uv run pyright CH_18_packaging/exercise_01
git add CH_18_packaging/exercise_01
git commit -m "feat: add setuptools version bump command"
```

Expected: all commands exit 0; pytest reports 7 parameterized cases/tests passing.

### Task 2: Interactive major/minor/patch command

**Files:**
- Create: `CH_18_packaging/exercise_02/__init__.py`
- Create: `CH_18_packaging/exercise_02/solution_00.py`
- Create: `CH_18_packaging/exercise_02/test_solution_00.py`

- [ ] **Step 1: Write failing prompt and subprocess tests**

```python
from __future__ import annotations

import shutil
import subprocess
import sys
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from CH_18_packaging.exercise_01.solution_00 import read_version
from .solution_00 import choose_version_part


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("major", "major"),
        ("2", "minor"),
        ("PATCH", "patch"),
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


@pytest.mark.timeout(30)
def test_interactive_command_uses_stdin(tmp_path: Path) -> None:
    package: Path = tmp_path / "demo_package"
    package.mkdir()
    (package / "__init__.py").write_text('__version__ = "1.2.3"\n', encoding="utf-8")
    shutil.copy(Path(__file__).with_name("solution_00.py"), tmp_path / "interactive_bump.py")
    (tmp_path / "setup.py").write_text(
        "from setuptools import setup\n"
        "from interactive_bump import InteractiveBumpVersion\n"
        "setup(name='demo-package', version='1.2.3', "
        "cmdclass={'bump_version': InteractiveBumpVersion})\n",
        encoding="utf-8",
    )
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
    assert read_version(package / "__init__.py") == "1.3.0"
```

- [ ] **Step 2: Run tests and verify the interactive command is absent**

Run `uv run --group packaging pytest CH_18_packaging/exercise_02/test_solution_00.py -vv`.

Expected: FAIL during import.

- [ ] **Step 3: Implement injectable choice parsing**

```python
from __future__ import annotations

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


def choose_version_part(input_function: Callable[[str], str] = input) -> VersionPart:
    answer: str = input_function(
        "Choose version bump: 1) major, 2) minor, 3) patch: "
    ).strip().lower()
    try:
        return CHOICES[answer]
    except KeyError as error:
        raise ValueError("choose major, minor, or patch") from error


class InteractiveBumpVersion(BumpVersion):
    description: str = "interactively choose and bump a package version"

    def finalize_options(self) -> None:
        if self.part is None or self.part == "interactive":
            self.part = choose_version_part()
        super().finalize_options()
```

Override `initialize_options()` so `part` defaults to `"interactive"` while retaining the inherited `version_file` field. Supplying `--part` must bypass input, allowing non-interactive automation.

- [ ] **Step 4: Add a test that an explicit part bypasses input**

Instantiate a `setuptools.Distribution`, create `InteractiveBumpVersion`, set a temporary version file and `part = "major"`, monkeypatch module `input` to raise if called, finalize, run, and assert `2.0.0`.

Expected initial failure: input is called despite explicit `--part`. Expected pass after the conditional implementation.

- [ ] **Step 5: Verify and commit**

```bash
uv run --group packaging pytest CH_18_packaging/exercise_02/test_solution_00.py -vv
uv run ruff format --check CH_18_packaging/exercise_02
uv run ruff check CH_18_packaging/exercise_02
uv run pyrefly check CH_18_packaging/exercise_02
uv run mypy CH_18_packaging/exercise_02
uv run pyright CH_18_packaging/exercise_02
git add CH_18_packaging/exercise_02
git commit -m "feat: add interactive version bump command"
```

Expected: every command exits 0 and pytest reports 6 parameterized cases/tests passing.

### Task 3: Static legacy metadata reader

**Files:**
- Create: `CH_18_packaging/exercise_03/__init__.py`
- Create: `CH_18_packaging/exercise_03/fixtures/legacy_project/setup.py`
- Create: `CH_18_packaging/exercise_03/fixtures/legacy_project/README.rst`
- Create: `CH_18_packaging/exercise_03/fixtures/legacy_project/greeting_demo/__init__.py`
- Create: `CH_18_packaging/exercise_03/solution_00.py`
- Create: `CH_18_packaging/exercise_03/test_solution_00.py`

- [ ] **Step 1: Add the intentionally legacy fixture**

`setup.py`:

```python
from setuptools import find_packages, setup


setup(
    name="greeting-demo",
    version="1.2.3",
    description="A tiny migration fixture",
    packages=find_packages(),
    python_requires=">=3.10",
    entry_points={"console_scripts": ["greet=greeting_demo:main"]},
)
```

`greeting_demo/__init__.py`:

```python
from __future__ import annotations

__version__: str = "1.2.3"


def greeting(name: str) -> str:
    return f"Hello, {name}!"


def main() -> None:
    print(greeting("packaging"))
```

`README.rst` contains a title and states that the fixture exists only for the migration exercise.

- [ ] **Step 2: Write failing metadata and security-boundary tests**

```python
from __future__ import annotations

from pathlib import Path

import pytest

from .solution_00 import ProjectMetadata, read_setup_metadata


FIXTURE: Path = Path(__file__).with_name("fixtures") / "legacy_project"


def test_read_setup_metadata_without_executing_setup() -> None:
    metadata: ProjectMetadata = read_setup_metadata(FIXTURE / "setup.py")
    assert metadata == ProjectMetadata(
        name="greeting-demo",
        version="1.2.3",
        description="A tiny migration fixture",
        requires_python=">=3.10",
        scripts={"greet": "greeting_demo:main"},
    )


def test_dynamic_setup_metadata_is_rejected(tmp_path: Path) -> None:
    setup_py: Path = tmp_path / "setup.py"
    setup_py.write_text(
        "from setuptools import setup\n"
        "setup(name=get_name(), version='1.0.0')\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="static literal"):
        read_setup_metadata(setup_py)
```

- [ ] **Step 3: Run tests and verify the parser is absent**

Run `uv run --group packaging pytest CH_18_packaging/exercise_03/test_solution_00.py -vv`.

Expected: FAIL during import.

- [ ] **Step 4: Implement a non-executing AST reader**

Expose:

```python
@dataclass(frozen=True)
class ProjectMetadata:
    name: str
    version: str
    description: str
    requires_python: str
    scripts: dict[str, str]


def read_setup_metadata(setup_py: Path) -> ProjectMetadata:
    """Read supported literal setup() keywords without executing setup.py."""
```

Parse with `ast.parse`; find exactly one call whose function is `setup` or an attribute named `setup`; accept only `name`, `version`, `description`, `python_requires`, and `entry_points` via `ast.literal_eval`. Reject `**kwargs`, duplicate setup calls, non-literal supported fields, absent required fields, and malformed `console_scripts`. Convert each `name=module:function` string to a mapping and validate that it has exactly one `=` and one `:`.

- [ ] **Step 5: Verify and commit the fixture/parser slice**

Run focused pytest and static checks, then:

```bash
git add CH_18_packaging/exercise_03
git commit -m "feat: parse static legacy setup metadata"
```

Expected: all commands exit 0 and pytest reports 2 passed.

### Task 4: Migrate, build, and inspect artifacts

**Files:**
- Modify: `CH_18_packaging/exercise_03/solution_00.py`
- Modify: `CH_18_packaging/exercise_03/test_solution_00.py`

- [ ] **Step 1: Add failing migration and build integration tests**

```python
from __future__ import annotations

import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from .solution_00 import migrate_project


@pytest.mark.timeout(90)
def test_migrated_project_builds_wheel_and_sdist(tmp_path: Path) -> None:
    source: Path = Path(__file__).with_name("fixtures") / "legacy_project"
    legacy_copy: Path = tmp_path / "legacy"
    shutil.copytree(source, legacy_copy)
    migrated: Path = migrate_project(legacy_copy, tmp_path / "migrated")
    assert not (migrated / "setup.py").exists()
    assert (migrated / "src" / "greeting_demo" / "__init__.py").is_file()

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

    with zipfile.ZipFile(wheels[0]) as archive:
        names: set[str] = set(archive.namelist())
        assert "greeting_demo/__init__.py" in names
        metadata_name: str = next(
            name for name in names if name.endswith(".dist-info/METADATA")
        )
        entry_points_name: str = next(
            name for name in names if name.endswith(".dist-info/entry_points.txt")
        )
        metadata: str = archive.read(metadata_name).decode()
        entry_points: str = archive.read(entry_points_name).decode()
    assert "Name: greeting-demo" in metadata
    assert "Version: 1.2.3" in metadata
    assert "greet = greeting_demo:main" in entry_points
```

- [ ] **Step 2: Run the integration test and verify `migrate_project` is missing**

Expected: FAIL during import or attribute lookup.

- [ ] **Step 3: Implement deterministic migration**

Expose:

```python
def migrate_project(source: Path, destination: Path) -> Path:
    if destination.exists():
        raise FileExistsError(destination)
    metadata: ProjectMetadata = read_setup_metadata(source / "setup.py")
    package_source: Path = source / metadata.name.replace("-", "_")
    if not package_source.is_dir():
        raise FileNotFoundError(package_source)

    package_destination: Path = destination / "src" / package_source.name
    package_destination.parent.mkdir(parents=True)
    shutil.copytree(package_source, package_destination)
    shutil.copy2(source / "README.rst", destination / "README.rst")
    (destination / "pyproject.toml").write_text(
        render_pyproject(metadata),
        encoding="utf-8",
    )
    return destination
```

`render_pyproject` returns deterministic TOML with JSON-quoted strings:

```toml
[build-system]
requires = ["setuptools>=77", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "greeting-demo"
version = "1.2.3"
description = "A tiny migration fixture"
readme = "README.rst"
requires-python = ">=3.10"

[project.scripts]
greet = "greeting_demo:main"

[tool.setuptools.packages.find]
where = ["src"]
```

Do not copy `setup.py`; do not execute it; do not mutate the source fixture.

- [ ] **Step 4: Add installed-wheel smoke coverage**

After building, import directly from the pure-Python wheel archive and call the console target:

```python
environment: dict[str, str] = os.environ.copy()
environment["PYTHONPATH"] = str(wheels[0])
smoke: subprocess.CompletedProcess[str] = subprocess.run(
    [
        sys.executable,
        "-c",
        "from greeting_demo import greeting, main; "
        "print(greeting('wheel')); main()",
    ],
    env=environment,
    check=False,
    capture_output=True,
    text=True,
    timeout=20,
)
assert smoke.returncode == 0, smoke.stderr
assert smoke.stdout.splitlines() == ["Hello, wheel!", "Hello, packaging!"]
```

This validates import and the function targeted by the console entry point without requiring pip in the uv environment.

- [ ] **Step 5: Verify and commit**

```bash
uv run --group packaging pytest CH_18_packaging/exercise_03/test_solution_00.py -vv
uv run ruff format --check CH_18_packaging/exercise_03
uv run ruff check CH_18_packaging/exercise_03
uv run pyrefly check CH_18_packaging/exercise_03
uv run mypy CH_18_packaging/exercise_03
uv run pyright CH_18_packaging/exercise_03
git status --short
git add CH_18_packaging/exercise_03/solution_00.py CH_18_packaging/exercise_03/test_solution_00.py
git commit -m "feat: migrate and build legacy fixture package"
```

Expected: all commands exit 0, status contains no `dist/`, `build/`, `*.egg-info`, wheel, or sdist, both artifacts exist only in pytest temporary storage, and the installed-wheel smoke test passes.

### Task 5: Per-exercise documentation and chapter links

**Files:**
- Create: `CH_18_packaging/exercise_01/README.rst`
- Create: `CH_18_packaging/exercise_02/README.rst`
- Create: `CH_18_packaging/exercise_03/README.rst`
- Modify: `CH_18_packaging/README.rst`

- [ ] **Step 1: Document exercise 1**

Repeat the exact setuptools-command question. Explain strict three-integer versions, all three bump parts, default patch behavior, designated-file-only writes, and the `packaging` dependency group. Include:

```console
uv run --group packaging pytest CH_18_packaging/exercise_01/test_solution_00.py -vv
```

Cite:

`https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_18_packaging/T_02_basic_setup_py/setup.py`

- [ ] **Step 2: Document exercise 2**

Repeat the exact interactive question. Explain accepted names/numbers, invalid-choice errors, stdin integration testing, and explicit `--part` automation. Include its focused uv pytest command and the same immutable setuptools reference.

- [ ] **Step 3: Document exercise 3**

Repeat the exact migration question. Explain the supported static metadata subset, refusal to execute setup code, `src` layout, temporary build, wheel/sdist inspection, installed-wheel smoke test, and no network. Cite:

- `CH_18_packaging/T_02_basic_setup_py/setup.py`
- `CH_18_packaging/T_00_basic_pyproject/pyproject.toml`

using the pinned GitHub commit URL.

- [ ] **Step 4: Link the chapter index and run packet checks**

Retain all exact question text and link items 1 through 3 to their exercise directories.

```bash
uv run --group packaging pytest CH_18_packaging -vv
uv run ruff format --check CH_18_packaging
uv run ruff check CH_18_packaging
uv run pyrefly check CH_18_packaging
uv run mypy CH_18_packaging
uv run pyright CH_18_packaging
```

Expected: every command exits 0.

- [ ] **Step 5: Commit documentation**

```bash
git add CH_18_packaging/README.rst CH_18_packaging/exercise_01/README.rst CH_18_packaging/exercise_02/README.rst CH_18_packaging/exercise_03/README.rst
git commit -m "docs: document packaging exercises"
```

## Packet acceptance

- [ ] Confirm all packaging/build operations occur on copied temporary fixtures.
- [ ] Confirm no test executes untrusted `setup.py` during metadata extraction.
- [ ] Confirm `python -m build --no-isolation` creates exactly one wheel and one sdist.
- [ ] Confirm wheel metadata, entry point, import, and console behavior are verified.
- [ ] Run the packet on Python 3.10 and 3.14 with no network access.
