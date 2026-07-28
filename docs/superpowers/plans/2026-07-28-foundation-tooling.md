# Repository Tooling Foundation Implementation

**For agentic workers:** REQUIRED SUB-SKILL: `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Use checkbox (`- [ ]`) steps.

**Goal:** Add reproducible Python 3.10 project metadata, locked dependencies, canonical quality checks, Lefthook hooks, CI, and contributor documentation.

**Architecture:** The repository remains a non-package uv project. Tool discovery includes all chapter Python files but excludes historical alternatives and fixture projects through centrally defined patterns; CI executes the same underlying commands as Lefthook.

**Tech Stack:** uv, Ruff, pytest, pytest-timeout, Pyrefly, mypy, Pyright, Lefthook, GitHub Actions.

---

### Task 1: Create the non-package uv project

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`
- Create: `uv.lock`

- [ ] **Step 1: Add the Python version marker**

Create `.python-version`:

```text
3.10
```

- [ ] **Step 2: Add project metadata and dependency groups**

Create `pyproject.toml`:

```toml
[project]
name = "mastering-python-exercises"
version = "0.1.0"
description = "Tested solutions for Mastering Python Second Edition exercises"
readme = "README.rst"
requires-python = ">=3.10"
dependencies = []

[dependency-groups]
dev = [
  "docutils>=0.21",
  "mypy>=1.18",
  "pyrefly>=0.59",
  "pyright>=1.1.411",
  "pyyaml>=6.0",
  "pytest>=9.0",
  "pytest-timeout>=2.4",
  "ruff>=0.15",
]
interactive = [
  "colorama>=0.4.6",
  "ipython>=8.37",
  "ipywidgets>=8.1",
  "jedi>=0.19",
]
scientific = [
  "datashader>=0.18",
  "nbclient>=0.10",
  "nbformat>=5.10",
  "numpy>=1.26",
  "pandas>=2.2",
]
nlp = [
  "spacy>=3.8",
]
native = [
  "build>=1.3",
  "cffi>=1.17",
  "setuptools>=80",
  "wheel>=0.45",
]
packaging = [
  "build>=1.3",
  "setuptools>=80",
  "tox>=4.30",
  "wheel>=0.45",
]

[tool.uv]
package = false
default-groups = ["dev"]
```

- [ ] **Step 3: Ignore generated local state**

Create `.gitignore`:

```gitignore
.DS_Store
.coverage
.mypy_cache/
.pytest_cache/
.pyrefly_cache/
.ruff_cache/
.tox/
.venv/
__pycache__/
build/
dist/
*.egg-info/
*.py[cod]
```

- [ ] **Step 4: Generate the cross-version lock**

Run:

```console
uv lock
```

Expected: exit code 0 and a new `uv.lock` that resolves all dependency groups
for the declared `>=3.10` range.

- [ ] **Step 5: Verify the locked Python 3.10 environment**

Run:

```console
uv sync --python 3.10 --locked --all-groups
uv run python --version
```

Expected: both commands exit 0; the version line starts with `Python 3.10.`.

- [ ] **Step 6: Commit project metadata**

```console
git add pyproject.toml .python-version .gitignore uv.lock
git commit -m "build: add locked Python exercise environment"
```

### Task 2: Configure formatting, linting, tests, and three type checkers

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add the shared exclusion and Ruff configuration**

Append to `pyproject.toml`:

```toml
[tool.ruff]
target-version = "py310"
line-length = 88
force-exclude = true
extend-exclude = [
  "**/fixtures/**",
  "**/multiprocessing_solution_00.py",
  "**/solution_[1-9][0-9].py",
  "**/threading_solution_00.py",
]

[tool.ruff.lint]
select = ["B", "E4", "E7", "E9", "F", "I", "RUF", "UP"]

[tool.ruff.format]
docstring-code-format = true
```

- [ ] **Step 2: Add deterministic pytest discovery**

Append:

```toml
[tool.pytest.ini_options]
addopts = [
  "--import-mode=importlib",
  "--strict-config",
  "--strict-markers",
  "--timeout=30",
]
python_files = ["test_solution_00.py"]
norecursedirs = ["fixtures"]
markers = [
  "integration: focused subprocess, notebook, plugin, or build integration",
  "native: tests requiring a working native compiler",
  "notebook: tests executing a notebook headlessly",
]
```

- [ ] **Step 3: Add strict mypy configuration**

Append:

```toml
[tool.mypy]
python_version = "3.10"
strict = true
show_error_codes = true
warn_unused_configs = true
exclude = [
  '(^|/)fixtures/',
  '(^|/)multiprocessing_solution_00\.py$',
  '(^|/)solution_[1-9][0-9]\.py$',
  '(^|/)threading_solution_00\.py$',
]
```

- [ ] **Step 4: Add strict Pyright configuration**

Append:

```toml
[tool.pyright]
pythonVersion = "3.10"
typeCheckingMode = "strict"
include = ["CH_*"]
exclude = [
  "**/fixtures/**",
  "**/multiprocessing_solution_00.py",
  "**/solution_[1-9][0-9].py",
  "**/threading_solution_00.py",
]
```

- [ ] **Step 5: Add Pyrefly configuration**

Append:

```toml
[tool.pyrefly]
python-version = "3.10"
project-includes = ["CH_*/**/*.py"]
project-excludes = [
  "**/fixtures/**",
  "**/multiprocessing_solution_00.py",
  "**/solution_[1-9][0-9].py",
  "**/threading_solution_00.py",
]
check-unannotated-defs = true
infer-return-types = "never"
```

- [ ] **Step 6: Verify every tool reads its configuration**

Run:

```console
uv run ruff check --show-settings CH_04_design_patterns/__init__.py
uv run pytest --collect-only
uv run mypy --no-incremental CH_04_design_patterns/__init__.py
uv run pyright CH_04_design_patterns/__init__.py --outputjson
uv run pyrefly dump-config
```

Expected: no configuration parse errors. Quality commands may report canonical
source findings until the chapter packets are complete; record those findings
without suppressing them.

- [ ] **Step 7: Commit quality configuration**

```console
git add pyproject.toml
git commit -m "build: configure canonical quality checks"
```

### Task 3: Add Lefthook commands

**Files:**
- Create: `lefthook.yml`

- [ ] **Step 1: Create the hook configuration**

Create `lefthook.yml`:

```yaml
pre-commit:
  parallel: false
  commands:
    format:
      glob: "**/*.py"
      run: uv run ruff format {staged_files}
      stage_fixed: true
    lint:
      glob: "**/*.py"
      run: uv run ruff check --fix {staged_files}
      stage_fixed: true

pre-push:
  parallel: true
  commands:
    mypy:
      run: uv run mypy .
    pyrefly:
      run: uv run pyrefly check
    pyright:
      run: uv run pyright
    pytest:
      run: uv run pytest
```

- [ ] **Step 2: Validate Lefthook parsing**

Run:

```console
lefthook validate
lefthook dump
```

Expected: both commands exit 0 and list `pre-commit` and `pre-push`.

- [ ] **Step 3: Commit the hook configuration**

```console
git add lefthook.yml
git commit -m "build: add Lefthook quality gates"
```

### Task 4: Add GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create the workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [master]
  pull_request:

permissions:
  contents: read

concurrency:
  group: ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  quality:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
      - uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9
        with:
          enable-cache: true
          python-version: "3.10"
      - run: uv sync --locked --all-groups
      - run: uv run ruff format --check .
      - run: uv run ruff check .
      - run: uv run pyrefly check
      - run: uv run mypy .
      - run: uv run pyright

  tests:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.10", "3.14"]
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1
      - uses: astral-sh/setup-uv@c771a70e6277c0a99b617c7a806ffedaca235ff9
        with:
          enable-cache: true
          python-version: ${{ matrix.python-version }}
      - run: uv sync --locked --all-groups
      - run: uv run pytest
```

- [ ] **Step 2: Parse the workflow as YAML**

Run:

```console
uv run python -c "import pathlib; import yaml; yaml.safe_load(pathlib.Path('.github/workflows/ci.yml').read_text())"
```

Expected: exit code 0.

- [ ] **Step 3: Commit CI**

```console
git add .github/workflows/ci.yml pyproject.toml uv.lock
git commit -m "ci: test canonical solutions and quality gates"
```

### Task 5: Replace the root contributor documentation

**Files:**
- Modify: `README.rst`

- [ ] **Step 1: Replace the README**

Use this complete structure and retain the existing invitation to submit
alternatives:

```rst
Mastering Python Second Edition Exercises
==========================================

This repository contains canonical and community solutions for all exercises
from *Mastering Python, Second Edition*.  ``solution_00.py`` is the maintained,
typed reference answer.  Higher-numbered and specialized solution files are
preserved community alternatives.

Requirements
------------

Python 3.10 or newer, uv, and Lefthook are required.  On macOS:

.. code-block:: console

   brew install uv lefthook
   uv sync --all-groups
   lefthook install

Running exercises
-----------------

Each ``exercise_NN`` directory contains its exact question, explanation,
canonical answer, dependencies, and focused tests.  Run one answer or test:

.. code-block:: console

   uv run python CH_04_design_patterns/exercise_01/solution_00.py
   uv run pytest CH_04_design_patterns/exercise_01/test_solution_00.py

Run all repository checks:

.. code-block:: console

   uv run ruff format --check .
   uv run ruff check .
   uv run pyrefly check
   uv run mypy .
   uv run pyright
   uv run pytest

Dependency groups
-----------------

``dev`` contains repository quality tools.  ``interactive``, ``scientific``,
``nlp``, ``native``, and ``packaging`` contain dependencies needed by their
respective chapter exercises.  ``uv sync --all-groups`` installs the complete
locked environment without runtime downloads.

Contributing
------------

Alternative solutions are welcome as the next available ``solution_NN.py``.
Keep canonical files, tests, and exercise documentation unchanged unless the
reference answer itself is being corrected.  All submitted Python code must be
formatted, linted, typed, and tested.
```

- [ ] **Step 2: Check README rendering syntax**

Run:

```console
uv run rst2html5 README.rst /tmp/mastering-python-exercises-readme.html
```

Expected: exit code 0 and no reStructuredText errors.

- [ ] **Step 3: Run foundation verification**

Run:

```console
uv lock --check
lefthook validate
uv run pytest --collect-only
git diff --check
```

Expected: the lock, Lefthook, and diff checks pass. Pytest collection lists
canonical tests added by completed packets, or exits 5 only when foundation is
executed before the first packet.

- [ ] **Step 4: Commit documentation**

```console
git add README.rst pyproject.toml uv.lock
git commit -m "docs: document exercise development workflow"
```
