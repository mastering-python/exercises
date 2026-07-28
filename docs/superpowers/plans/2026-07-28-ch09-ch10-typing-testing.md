# Chapters 9-10 Typing, Testing, and Logging Implementation

**For agentic workers:** REQUIRED SUB-SKILL: Use
`superpowers:subagent-driven-development` (recommended) or
`superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Add canonical typed examples for all three Chapter 9 prompts and
offline-tested implementations for all five Chapter 10 prompts.

**Architecture:** Chapter 9 uses one focused runtime example per typing concept:
a heterogeneous `TypedDict`, a deeply nested type alias, and a recursive tree
alias. Chapter 10 exposes reusable doctest runners, a modern pytest collection
hook, a generated tox configuration that runs offline from the locked
environment, and a thread-safe `LoggerAdapter` message buffer.

**Tech Stack:** Python 3.10, `typing`, doctest, pytest/pytester, tox 4, flake8,
mypy, logging, Ruff, Pyrefly, Pyright

---

## File map and fixed public APIs

- CH09 Exercise 1: `Contact`, `UserRecord`, `describe_user`
- CH09 Exercise 2: `NestedMeasurements`, `flatten_measurements`
- CH09 Exercise 3: `Tree`, `count_nodes`
- CH10 Exercise 1: `run_doctests`
- CH10 Exercise 2: `run_module_doctests`
- CH10 Exercise 3: `has_module_docstring`, `pytest_collect_file`
- CH10 Exercise 4: `render_tox_config`, `write_tox_config`
- CH10 Exercise 5: `TaskLoggerAdapter.add`, `TaskLoggerAdapter.flush`
- Every exercise directory contains `__init__.py`, `README.rst`,
  `solution_00.py`, and `test_solution_00.py`.
- The coordinator owns root dependency/static-check configuration. Do not
  modify root configuration from this packet.

### Task 1: Type a heterogeneous complex dictionary

**Files:**

- Create: `CH_09_documentation/exercise_01/__init__.py`
- Create: `CH_09_documentation/exercise_01/solution_00.py`
- Create: `CH_09_documentation/exercise_01/test_solution_00.py`
- Create: `CH_09_documentation/exercise_01/README.rst`

- [ ] **Step 1: Write the failing runtime and annotation tests**

```python
# CH_09_documentation/exercise_01/test_solution_00.py
from typing import get_type_hints

from CH_09_documentation.exercise_01.solution_00 import (
    Contact,
    UserRecord,
    describe_user,
)


def test_describe_user_reads_heterogeneous_record() -> None:
    user: UserRecord = {
        "name": "Ada",
        "age": 36,
        "active": True,
        "contact": {"email": "ada@example.test", "phone": None},
    }

    assert describe_user(user) == "Ada (36) active: ada@example.test"


def test_typed_dict_exposes_nested_field_types() -> None:
    user_hints: dict[str, object] = get_type_hints(UserRecord)
    contact_hints: dict[str, object] = get_type_hints(Contact)

    assert set(user_hints) == {"name", "age", "active", "contact"}
    assert set(contact_hints) == {"email", "phone"}
```

- [ ] **Step 2: Run the missing-module test**

Run:

```bash
uv run pytest CH_09_documentation/exercise_01/test_solution_00.py -v
```

Expected: FAIL during collection with `ModuleNotFoundError` because the exercise
directory does not exist.

- [ ] **Step 3: Add the typed dictionary implementation**

```python
# CH_09_documentation/exercise_01/solution_00.py
"""Type a dictionary whose values have different, known shapes."""

from typing import TypedDict


class Contact(TypedDict):
    """Contact fields nested in a user record."""

    email: str
    phone: str | None


class UserRecord(TypedDict):
    """A heterogeneous dictionary with a nested typed dictionary."""

    name: str
    age: int
    active: bool
    contact: Contact


def describe_user(user: UserRecord) -> str:
    """Render the fields while preserving their precise static types."""
    state: str = "active" if user["active"] else "inactive"
    return (
        f'{user["name"]} ({user["age"]}) {state}: '
        f'{user["contact"]["email"]}'
    )


def main() -> None:
    """Render one fully typed record."""
    user: UserRecord = {
        "name": "Ada",
        "age": 36,
        "active": True,
        "contact": {"email": "ada@example.test", "phone": None},
    }
    print(describe_user(user))


if __name__ == "__main__":
    main()
```

Create an empty `CH_09_documentation/exercise_01/__init__.py`.

- [ ] **Step 4: Verify runtime and strict typing**

Run:

```bash
uv run pytest CH_09_documentation/exercise_01/test_solution_00.py -v
uv run mypy CH_09_documentation/exercise_01/solution_00.py
uv run pyright CH_09_documentation/exercise_01/solution_00.py
uv run pyrefly check CH_09_documentation/exercise_01/solution_00.py
```

Expected: two tests pass and all three type checkers exit zero.

- [ ] **Step 5: Add README and commit**

The README must repeat “Type hint a complex `dict`,” explain why `TypedDict`
fits heterogeneous fixed keys, list standard-library/pytest dependencies, and
show:

```console
uv run python -m CH_09_documentation.exercise_01.solution_00
uv run pytest CH_09_documentation/exercise_01/test_solution_00.py -v
```

Include this immutable source:

```rst
`Upstream type-hinting examples <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_09_documentation/T_00_type_hinting.rst>`_
```

Run:

```bash
git add CH_09_documentation/exercise_01
git commit -m "feat: add complex dictionary typing exercise"
```

Expected: the commit contains only CH09 Exercise 1.

### Task 2: Type deeply nested containers

**Files:**

- Create: `CH_09_documentation/exercise_02/__init__.py`
- Create: `CH_09_documentation/exercise_02/solution_00.py`
- Create: `CH_09_documentation/exercise_02/test_solution_00.py`
- Create: `CH_09_documentation/exercise_02/README.rst`

- [ ] **Step 1: Write the failing nested-container tests**

```python
# CH_09_documentation/exercise_02/test_solution_00.py
from CH_09_documentation.exercise_02.solution_00 import (
    NestedMeasurements,
    flatten_measurements,
)


def test_flatten_measurements_preserves_mapping_and_list_order() -> None:
    values: NestedMeasurements = {
        "north": [(1, 1.5), (2, 2.5)],
        "south": [(3, 3.5)],
    }

    assert flatten_measurements(values) == [1.5, 2.5, 3.5]


def test_flatten_measurements_accepts_empty_levels() -> None:
    values: NestedMeasurements = {"north": [], "south": []}

    assert flatten_measurements(values) == []
```

- [ ] **Step 2: Confirm the test fails before implementation**

Run:

```bash
uv run pytest CH_09_documentation/exercise_02/test_solution_00.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the nested alias and consumer**

```python
# CH_09_documentation/exercise_02/solution_00.py
"""Type nested homogeneous containers with a readable alias."""

from typing import TypeAlias

NestedMeasurements: TypeAlias = dict[str, list[tuple[int, float]]]


def flatten_measurements(values: NestedMeasurements) -> list[float]:
    """Return each measurement value in deterministic insertion order."""
    flattened: list[float] = []
    rows: list[tuple[int, float]]
    measurement: float
    for rows in values.values():
        for _, measurement in rows:
            flattened.append(measurement)
    return flattened


def main() -> None:
    """Demonstrate the nested alias."""
    values: NestedMeasurements = {"north": [(1, 1.5), (2, 2.5)]}
    print(flatten_measurements(values))


if __name__ == "__main__":
    main()
```

Create an empty `__init__.py`.

- [ ] **Step 4: Run tests, type checks, document, and commit**

Run:

```bash
uv run pytest CH_09_documentation/exercise_02/test_solution_00.py -v
uv run mypy CH_09_documentation/exercise_02/solution_00.py
uv run pyright CH_09_documentation/exercise_02/solution_00.py
uv run pyrefly check CH_09_documentation/exercise_02/solution_00.py
```

Expected: two tests pass and strict checks exit zero.

Create `README.rst` with the exact question “Type hint nested types,” explain
the alias and deterministic order, cite `T_00_type_hinting.rst` at the pinned
SHA, and show:

```console
uv run python -m CH_09_documentation.exercise_02.solution_00
uv run pytest CH_09_documentation/exercise_02/test_solution_00.py -v
```

Then:

```bash
git add CH_09_documentation/exercise_02
git commit -m "feat: add nested type exercise"
```

### Task 3: Type and safely traverse a recursive tree

**Files:**

- Create: `CH_09_documentation/exercise_03/__init__.py`
- Create: `CH_09_documentation/exercise_03/solution_00.py`
- Create: `CH_09_documentation/exercise_03/test_solution_00.py`
- Create: `CH_09_documentation/exercise_03/README.rst`
- Modify: `CH_09_documentation/README.rst`

- [ ] **Step 1: Write recursive and cycle tests**

```python
# CH_09_documentation/exercise_03/test_solution_00.py
import pytest

from CH_09_documentation.exercise_03.solution_00 import Tree, count_nodes


def test_count_nodes_handles_nested_and_empty_branches() -> None:
    tree: Tree = {
        "root": {
            "left": {},
            "right": {"leaf": {}},
        }
    }

    assert count_nodes(tree) == 4
    assert count_nodes({}) == 0


def test_count_nodes_rejects_a_cycle() -> None:
    tree: Tree = {}
    tree["loop"] = tree

    with pytest.raises(ValueError, match="tree contains a cycle"):
        count_nodes(tree)
```

- [ ] **Step 2: Run and observe the missing-module failure**

Run:

```bash
uv run pytest CH_09_documentation/exercise_03/test_solution_00.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement a forward-referenced recursive alias**

```python
# CH_09_documentation/exercise_03/solution_00.py
"""Represent and traverse a recursively nested tree."""

from typing import TypeAlias

Tree: TypeAlias = dict[str, "Tree"]


def count_nodes(tree: Tree) -> int:
    """Count named nodes and reject reference cycles."""

    def visit(branch: Tree, ancestors: set[int]) -> int:
        branch_id: int = id(branch)
        if branch_id in ancestors:
            raise ValueError("tree contains a cycle")
        next_ancestors: set[int] = ancestors | {branch_id}
        total: int = 0
        name: str
        children: Tree
        for name, children in branch.items():
            del name
            total += 1 + visit(children, next_ancestors)
        return total

    return visit(tree, set())


def main() -> None:
    """Count one recursive example."""
    tree: Tree = {"root": {"leaf": {}}}
    print(count_nodes(tree))


if __name__ == "__main__":
    main()
```

Create the empty package initializer.

- [ ] **Step 4: Verify, document, index, and commit**

Run:

```bash
uv run pytest CH_09_documentation/exercise_03/test_solution_00.py -v
uv run ruff format --check CH_09_documentation
uv run ruff check CH_09_documentation
uv run pyrefly check CH_09_documentation
uv run mypy CH_09_documentation
uv run pyright CH_09_documentation
```

Expected: recursive tests pass and all checks exit zero.

The exercise README repeats “Type hint recursive types,” documents the
dictionary-tree interpretation and cycle error, lists standard-library/pytest
dependencies, shows the module/test commands, and cites pinned
`T_00_type_hinting.rst`. Replace the chapter README with:

```rst
Chapter 9 - documentation
=========================

1. `Complex dictionaries <exercise_01/>`_
2. `Nested container types <exercise_02/>`_
3. `Recursive types <exercise_03/>`_
```

Commit:

```bash
git add CH_09_documentation/exercise_03 CH_09_documentation/README.rst
git commit -m "feat: add recursive type exercise"
```

### Task 4: Run doctests attached to one function or class

**Files:**

- Create: `CH_10_testing_and_logging/exercise_01/__init__.py`
- Create: `CH_10_testing_and_logging/exercise_01/solution_00.py`
- Create: `CH_10_testing_and_logging/exercise_01/test_solution_00.py`
- Create: `CH_10_testing_and_logging/exercise_01/README.rst`

- [ ] **Step 1: Write passing, failing, and empty-doctest tests**

```python
# CH_10_testing_and_logging/exercise_01/test_solution_00.py
import doctest

from CH_10_testing_and_logging.exercise_01.solution_00 import run_doctests


def documented_add(left: int, right: int) -> int:
    """Add two values.

    >>> documented_add(2, 3)
    5
    """
    return left + right


def broken_example() -> int:
    """Expose a deliberately failing doctest.

    >>> broken_example()
    2
    """
    return 1


def test_run_doctests_reports_success() -> None:
    result: doctest.TestResults = run_doctests(documented_add)

    assert result == doctest.TestResults(failed=0, attempted=1)


def test_run_doctests_reports_failure_without_swallowing_it() -> None:
    result: doctest.TestResults = run_doctests(broken_example)

    assert result.failed == 1
    assert result.attempted == 1


def test_run_doctests_accepts_object_without_examples() -> None:
    result: doctest.TestResults = run_doctests(object)

    assert result == doctest.TestResults(failed=0, attempted=0)
```

- [ ] **Step 2: Run the test and see the missing implementation**

Run:

```bash
uv run pytest CH_10_testing_and_logging/exercise_01/test_solution_00.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the focused doctest runner**

```python
# CH_10_testing_and_logging/exercise_01/solution_00.py
"""Run doctests attached to a function, class, or other object."""

import doctest


def run_doctests(
    target: object,
    *,
    optionflags: int = doctest.ELLIPSIS,
) -> doctest.TestResults:
    """Run every doctest found below one target and return totals."""
    finder: doctest.DocTestFinder = doctest.DocTestFinder(recurse=True)
    runner: doctest.DocTestRunner = doctest.DocTestRunner(
        optionflags=optionflags
    )
    test: doctest.DocTest
    for test in finder.find(target):
        runner.run(test)
    return runner.summarize(verbose=False)


if __name__ == "__main__":
    raise SystemExit("Import run_doctests and pass a documented object.")
```

Create the empty package initializer.

- [ ] **Step 4: Verify, document, and commit**

Run:

```bash
uv run pytest CH_10_testing_and_logging/exercise_01/test_solution_00.py -v
uv run ruff check CH_10_testing_and_logging/exercise_01
uv run mypy CH_10_testing_and_logging/exercise_01/solution_00.py
uv run pyright CH_10_testing_and_logging/exercise_01/solution_00.py
```

Expected: three tests pass and checks exit zero.

README requirements: exact prompt, explain returned attempted/failed totals,
list pytest, show the focused `uv run pytest` command, and cite:

```rst
`Simple doctest example <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_10_testing_and_logging/T_00_simple_doctest.py>`_
```

Commit:

```bash
git add CH_10_testing_and_logging/exercise_01
git commit -m "feat: add object doctest runner"
```

### Task 5: Recursively run doctests in a module

**Files:**

- Create: `CH_10_testing_and_logging/exercise_02/__init__.py`
- Create: `CH_10_testing_and_logging/exercise_02/solution_00.py`
- Create: `CH_10_testing_and_logging/exercise_02/test_solution_00.py`
- Create: `CH_10_testing_and_logging/exercise_02/README.rst`

- [ ] **Step 1: Write a synthetic-module integration test**

```python
# CH_10_testing_and_logging/exercise_02/test_solution_00.py
import doctest
import types

import pytest

from CH_10_testing_and_logging.exercise_02.solution_00 import (
    run_module_doctests,
)


def make_module() -> types.ModuleType:
    module: types.ModuleType = types.ModuleType("doctest_fixture")
    source: str = '''
def square(value: int) -> int:
    """Square a value.

    >>> square(4)
    16
    """
    return value * value

class Calculator:
    """A documented class.

    >>> Calculator().double(3)
    6
    """
    def double(self, value: int) -> int:
        return value * 2
'''
    exec(compile(source, "<doctest_fixture>", "exec"), module.__dict__)
    return module


def test_run_module_doctests_recurses_into_functions_and_classes() -> None:
    result: doctest.TestResults = run_module_doctests(make_module())

    assert result == doctest.TestResults(failed=0, attempted=2)


def test_run_module_doctests_rejects_non_module() -> None:
    with pytest.raises(TypeError, match="target must be a module"):
        run_module_doctests(object())
```

- [ ] **Step 2: Run and confirm failure**

Run:

```bash
uv run pytest CH_10_testing_and_logging/exercise_02/test_solution_00.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement recursive module discovery**

```python
# CH_10_testing_and_logging/exercise_02/solution_00.py
"""Run all function and class doctests owned by a module."""

import doctest
import types


def run_module_doctests(target: object) -> doctest.TestResults:
    """Recursively discover and run doctests in one module."""
    if not isinstance(target, types.ModuleType):
        raise TypeError("target must be a module")
    finder: doctest.DocTestFinder = doctest.DocTestFinder(recurse=True)
    runner: doctest.DocTestRunner = doctest.DocTestRunner()
    test: doctest.DocTest
    for test in finder.find(
        target,
        name=target.__name__,
        module=target,
    ):
        runner.run(test)
    return runner.summarize(verbose=False)


if __name__ == "__main__":
    raise SystemExit("Import run_module_doctests and pass a module.")
```

- [ ] **Step 4: Verify, document, and commit**

Run:

```bash
uv run pytest CH_10_testing_and_logging/exercise_02/test_solution_00.py -v
uv run ruff check CH_10_testing_and_logging/exercise_02
uv run pyrefly check CH_10_testing_and_logging/exercise_02
uv run mypy CH_10_testing_and_logging/exercise_02
uv run pyright CH_10_testing_and_logging/exercise_02
```

Expected: two tests pass and every check exits zero.

README: repeat the recursive-doctest prompt, state that only objects owned by
the module are discovered, list pytest, show the exact focused command, and cite
the pinned `T_00_simple_doctest.py` and `T_02_testing_with_documentation/`
sources. Commit as:

```bash
git add CH_10_testing_and_logging/exercise_02
git commit -m "feat: add recursive module doctest runner"
```

### Task 6: Enforce module docstrings with a pytest plugin

**Files:**

- Create: `CH_10_testing_and_logging/exercise_03/__init__.py`
- Create: `CH_10_testing_and_logging/exercise_03/solution_00.py`
- Create: `CH_10_testing_and_logging/exercise_03/test_solution_00.py`
- Create: `CH_10_testing_and_logging/exercise_03/README.rst`

- [ ] **Step 1: Write pytester integration tests**

```python
# CH_10_testing_and_logging/exercise_03/test_solution_00.py
import pytest

pytest_plugins: tuple[str, ...] = ("pytester",)


def install_plugin(pytester: pytest.Pytester) -> None:
    pytester.makeconftest(
        'pytest_plugins = '
        '("CH_10_testing_and_logging.exercise_03.solution_00",)'
    )


def test_documented_test_module_collects(pytester: pytest.Pytester) -> None:
    install_plugin(pytester)
    pytester.makepyfile(
        test_documented='''"""Documented test module."""

def test_ok() -> None:
    assert True
'''
    )

    result: pytest.RunResult = pytester.runpytest("-q")

    result.assert_outcomes(passed=1)


def test_undocumented_test_module_is_rejected(
    pytester: pytest.Pytester,
) -> None:
    install_plugin(pytester)
    pytester.makepyfile(
        test_undocumented="""def test_ok() -> None:
    assert True
"""
    )

    result: pytest.RunResult = pytester.runpytest("-q")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(
        ["*test_undocumented.py is missing a module docstring*"]
    )
```

- [ ] **Step 2: Run and confirm the plugin does not exist**

Run:

```bash
uv run pytest CH_10_testing_and_logging/exercise_03/test_solution_00.py -v
```

Expected: both pytester subprocesses fail to import the plugin.

- [ ] **Step 3: Implement the modern pathlib-based collection hook**

```python
# CH_10_testing_and_logging/exercise_03/solution_00.py
"""Pytest plugin requiring a file-level docstring in Python test modules."""

import ast
from pathlib import Path

import pytest


def has_module_docstring(path: Path) -> bool:
    """Return whether a Python source file starts with a module docstring."""
    source: str = path.read_text(encoding="utf-8")
    module: ast.Module = ast.parse(source, filename=str(path))
    return ast.get_docstring(module, clean=False) is not None


def _is_test_module(path: Path) -> bool:
    return path.suffix == ".py" and (
        path.name.startswith("test_") or path.name.endswith("_test.py")
    )


def pytest_collect_file(
    file_path: Path,
    parent: pytest.Collector,
) -> None:
    """Reject collected Python test modules without file documentation."""
    del parent
    if _is_test_module(file_path) and not has_module_docstring(file_path):
        raise pytest.UsageError(
            f"{file_path.name} is missing a module docstring"
        )
```

This uses pytest's `pathlib.Path` hook argument, not the legacy `py.path`
argument. It checks test modules only, so loading `conftest.py` does not
recursively reject the plugin setup itself.

- [ ] **Step 4: Verify integration, document, and commit**

Run:

```bash
uv run pytest CH_10_testing_and_logging/exercise_03/test_solution_00.py -v
uv run ruff check CH_10_testing_and_logging/exercise_03
uv run pyrefly check CH_10_testing_and_logging/exercise_03
uv run mypy CH_10_testing_and_logging/exercise_03
uv run pyright CH_10_testing_and_logging/exercise_03
```

Expected: two outer tests pass; the nested undocumented project exits with
pytest usage error; static checks pass.

README: exact prompt, test-module scope, syntax-error propagation, pytest
dependency, focused command, and pinned references to upstream
`CH_10_testing_and_logging/conftest.py` and `T_19_pytest.ini`. Commit:

```bash
git add CH_10_testing_and_logging/exercise_03
git commit -m "feat: add pytest documentation plugin"
```

### Task 7: Generate and execute an offline tox quality environment

**Files:**

- Create: `CH_10_testing_and_logging/exercise_04/__init__.py`
- Create: `CH_10_testing_and_logging/exercise_04/solution_00.py`
- Create: `CH_10_testing_and_logging/exercise_04/test_solution_00.py`
- Create: `CH_10_testing_and_logging/exercise_04/README.rst`

- [ ] **Step 1: Write config and tox integration tests**

```python
# CH_10_testing_and_logging/exercise_04/test_solution_00.py
import subprocess
import sys
from pathlib import Path

from CH_10_testing_and_logging.exercise_04.solution_00 import (
    render_tox_config,
    write_tox_config,
)


def test_render_tox_config_has_flake8_and_mypy_environments() -> None:
    config: str = render_tox_config("sample.py")

    assert "env_list = flake8, mypy" in config
    assert "python -m flake8 sample.py" in config
    assert "python -m mypy sample.py" in config
    assert "system_site_packages = true" in config


def test_generated_tox_config_passes_offline(tmp_path: Path) -> None:
    source: Path = tmp_path / "sample.py"
    source.write_text(
        '"""Typed sample."""\n\nvalue: int = 3\n',
        encoding="utf-8",
    )
    config: Path = write_tox_config(tmp_path, "sample.py")

    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "tox",
            "run",
            "--no-provision",
            "-c",
            str(config),
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
```

- [ ] **Step 2: Run and confirm the missing implementation**

Run:

```bash
uv run pytest CH_10_testing_and_logging/exercise_04/test_solution_00.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement deterministic config generation**

```python
# CH_10_testing_and_logging/exercise_04/solution_00.py
"""Generate a tox configuration that runs flake8 and mypy offline."""

from pathlib import Path, PurePath


def render_tox_config(target: str) -> str:
    """Render tox 4 configuration for one relative Python path."""
    target_path: PurePath = PurePath(target)
    if target_path.is_absolute() or ".." in target_path.parts:
        raise ValueError("target must be a relative path inside the project")
    if any(character.isspace() for character in target):
        raise ValueError("target must not contain whitespace")
    return f"""[tox]
env_list = flake8, mypy
skipsdist = true

[testenv]
package = skip
system_site_packages = true

[testenv:flake8]
commands = python -m flake8 {target}

[testenv:mypy]
commands = python -m mypy {target}
"""


def write_tox_config(directory: Path, target: str) -> Path:
    """Write the generated configuration and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    config_path: Path = directory / "tox.ini"
    config_path.write_text(render_tox_config(target), encoding="utf-8")
    return config_path


if __name__ == "__main__":
    print(render_tox_config("sample.py"))
```

The tox environments inherit only the already locked uv environment and
declare no tox dependencies, so the integration test cannot trigger package
downloads.

- [ ] **Step 4: Verify success and representative failure**

Append this complete regression test:

```python
def test_generated_tox_config_reports_mypy_failure(tmp_path: Path) -> None:
    source: Path = tmp_path / "sample.py"
    source.write_text(
        '"""Invalid typed sample."""\n\nvalue: str = 3\n',
        encoding="utf-8",
    )
    config: Path = write_tox_config(tmp_path, "sample.py")

    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "tox",
            "run",
            "--no-provision",
            "-c",
            str(config),
            "-e",
            "mypy",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
        timeout=60,
    )

    output: str = completed.stdout + completed.stderr
    assert completed.returncode != 0
    assert "assignment" in output
```

Then run:

```bash
uv run pytest CH_10_testing_and_logging/exercise_04/test_solution_00.py -v
```

Expected: config test and valid integration pass; invalid source produces the
asserted nonzero tox result while the outer pytest test passes.

- [ ] **Step 5: Document and commit**

README: exact tox prompt; explain `flake8` is intentionally used even though
the repository uses Ruff; state the inherited locked-environment/offline
choice; list tox, flake8, mypy, pytest; show the focused test command; cite
`T_22_tox/tox.ini` and `T_19_pytest.ini` at the pinned upstream SHA.

Run Ruff and all three type checkers, then:

```bash
git add CH_10_testing_and_logging/exercise_04
git commit -m "feat: add tox quality environment exercise"
```

### Task 8: Buffer task messages in a LoggerAdapter

**Files:**

- Create: `CH_10_testing_and_logging/exercise_05/__init__.py`
- Create: `CH_10_testing_and_logging/exercise_05/solution_00.py`
- Create: `CH_10_testing_and_logging/exercise_05/test_solution_00.py`
- Create: `CH_10_testing_and_logging/exercise_05/README.rst`
- Modify: `CH_10_testing_and_logging/README.rst`

- [ ] **Step 1: Write isolation, ordering, and failure tests**

```python
# CH_10_testing_and_logging/exercise_05/test_solution_00.py
import logging

import pytest

from CH_10_testing_and_logging.exercise_05.solution_00 import (
    TaskLoggerAdapter,
)


def test_flush_combines_only_one_task_in_order(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger: logging.Logger = logging.getLogger("task-buffer-test")
    adapter: TaskLoggerAdapter = TaskLoggerAdapter(logger)
    adapter.add("a", "first %s", "message")
    adapter.add("b", "other")
    adapter.add("a", "second")

    with caplog.at_level(logging.INFO, logger=logger.name):
        combined: str = adapter.flush("a")

    assert combined == "first message\nsecond"
    assert [record.getMessage() for record in caplog.records] == [combined]
    assert getattr(caplog.records[0], "task_id") == "a"
    assert adapter.pending("b") == 1


def test_flush_unknown_task_raises_key_error() -> None:
    adapter: TaskLoggerAdapter = TaskLoggerAdapter(
        logging.getLogger("empty-task-buffer")
    )

    with pytest.raises(KeyError, match="missing"):
        adapter.flush("missing")


def test_empty_task_id_is_rejected() -> None:
    adapter: TaskLoggerAdapter = TaskLoggerAdapter(
        logging.getLogger("invalid-task-buffer")
    )

    with pytest.raises(ValueError, match="task_id must not be empty"):
        adapter.add("", "message")
```

- [ ] **Step 2: Run and observe the missing-module failure**

Run:

```bash
uv run pytest CH_10_testing_and_logging/exercise_05/test_solution_00.py -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement the thread-safe adapter**

```python
# CH_10_testing_and_logging/exercise_05/solution_00.py
"""Combine buffered messages into one log record per task identifier."""

import logging
import threading
from collections.abc import Mapping


class TaskLoggerAdapter(logging.LoggerAdapter):
    """Buffer ordered messages separately for each task."""

    def __init__(
        self,
        logger: logging.Logger,
        extra: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(logger, dict(extra or {}))
        self._messages: dict[str, list[str]] = {}
        self._lock: threading.Lock = threading.Lock()

    def add(
        self,
        task_id: str,
        message: str,
        *args: object,
    ) -> None:
        """Format and append one message without emitting a record."""
        if not task_id:
            raise ValueError("task_id must not be empty")
        formatted: str = message % args if args else message
        with self._lock:
            self._messages.setdefault(task_id, []).append(formatted)

    def pending(self, task_id: str) -> int:
        """Return the number of buffered messages for a task."""
        with self._lock:
            return len(self._messages.get(task_id, ()))

    def flush(
        self,
        task_id: str,
        *,
        level: int = logging.INFO,
    ) -> str:
        """Emit and return one newline-joined record for a task."""
        with self._lock:
            try:
                messages: list[str] = self._messages.pop(task_id)
            except KeyError:
                raise KeyError(task_id) from None
        combined: str = "\n".join(messages)
        record_extra: dict[str, object] = dict(self.extra)
        record_extra["task_id"] = task_id
        self.logger.log(level, combined, extra=record_extra)
        return combined


def main() -> None:
    """Demonstrate buffering two messages into one record."""
    logging.basicConfig(level=logging.INFO)
    adapter: TaskLoggerAdapter = TaskLoggerAdapter(
        logging.getLogger(__name__)
    )
    adapter.add("demo", "first")
    adapter.add("demo", "second")
    adapter.flush("demo")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests and packet quality checks**

Run:

```bash
uv run pytest CH_10_testing_and_logging/exercise_05/test_solution_00.py -v
uv run ruff format --check CH_10_testing_and_logging
uv run ruff check CH_10_testing_and_logging
uv run pyrefly check CH_10_testing_and_logging
uv run mypy CH_10_testing_and_logging
uv run pyright CH_10_testing_and_logging
```

Expected: three tests pass and all quality commands exit zero.

- [ ] **Step 5: Document, index, and commit**

README: exact LoggerAdapter prompt; ordered per-task buffering, explicit flush,
unknown-task/empty-ID behavior, logging/pytest dependencies, module/test
commands, and pinned `T_33_logging_format.py`.

Replace `CH_10_testing_and_logging/README.rst` with:

```rst
Chapter 10 - testing and logging
================================

1. `Object doctests <exercise_01/>`_
2. `Recursive module doctests <exercise_02/>`_
3. `File-documentation pytest plugin <exercise_03/>`_
4. `Tox flake8 and mypy environments <exercise_04/>`_
5. `Task-aware LoggerAdapter <exercise_05/>`_
```

Commit:

```bash
git add CH_10_testing_and_logging/exercise_05 CH_10_testing_and_logging/README.rst
git commit -m "feat: add task-aware logging adapter exercise"
```

### Task 9: Packet acceptance check

**Files:**

- Review: `CH_09_documentation/`
- Review: `CH_10_testing_and_logging/`

- [ ] **Step 1: Verify directory contracts and placeholders**

Run:

```bash
find CH_09_documentation CH_10_testing_and_logging -maxdepth 2 -type f | sort
```

Expected: every exercise has the four required files; placeholder search has no
matches.

- [ ] **Step 2: Run the complete packet**

Run:

```bash
uv run pytest CH_09_documentation CH_10_testing_and_logging -v
uv run ruff format --check CH_09_documentation CH_10_testing_and_logging
uv run ruff check CH_09_documentation CH_10_testing_and_logging
uv run pyrefly check CH_09_documentation CH_10_testing_and_logging
uv run mypy CH_09_documentation CH_10_testing_and_logging
uv run pyright CH_09_documentation CH_10_testing_and_logging
```

Expected: all tests pass, including nested pytest and tox integration; all
static checks exit zero; no network access occurs.

- [ ] **Step 3: Confirm ownership isolation**

Run:

```bash
git status --short
git diff --stat master -- CH_09_documentation CH_10_testing_and_logging
```

Expected: no uncommitted packet changes and no historical alternative or
outside-packet file was changed.
