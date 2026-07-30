# Complete Python 3.10 Exercise Solutions

## Goal

Provide a high-quality, Python 3.10-compatible canonical answer for all 56
substantive exercises in this repository. Every answer must be documented,
explicitly typed, automatically tested with pytest, and reproducible from a
clean checkout.

The repository will also gain locked development dependencies, Ruff formatting
and linting, strict checks with Pyrefly, mypy, and Pyright, Lefthook Git hooks,
and GitHub Actions CI.

## Existing Content

The repository has 18 chapter directories and 56 substantive exercises.
Chapters 1 and 3 explicitly have no exercises. Existing coverage is incomplete:
28 exercise directories contain 33 answer files, including 24 reference
`solution_00.py` files and several contributed alternatives.

Existing contributed alternatives are historical material. They must remain
unchanged:

- `solution_01.py` and future numbered alternatives
- `threading_solution_00.py`
- `multiprocessing_solution_00.py`

Existing `solution_00.py` files are the canonical reference answers and may be
rewritten to satisfy this design.

## Exercise Directory Contract

Create every missing `exercise_NN/` directory. Each exercise directory must
contain:

- `__init__.py`
- `README.rst`
- `solution_00.py`
- `test_solution_00.py`
- only the minimal support files or fixtures required by that exercise

Each `README.rst` must:

1. Repeat the exact exercise question from the chapter README.
2. Explain briefly what the answer is expected to do.
3. State important behavioral choices and edge cases.
4. List exercise-specific dependencies.
5. Show commands for running the answer and its tests with `uv run`.
6. Cite immutable upstream references where they informed the answer.

Chapter READMEs remain concise exercise indexes and link to their exercise
directories.

## Canonical Solution Contract

Each `solution_00.py` must:

- parse and run on Python 3.10;
- annotate all variables, function signatures, attributes, and public return
  values explicitly;
- remain import-safe, with demonstrations guarded by
  `if __name__ == "__main__":`;
- expose reusable functions or classes rather than hiding behavior in a script;
- preserve existing public names when they remain compatible with the prompt;
- use deterministic behavior unless nondeterminism is intrinsic to the
  exercise;
- raise specific built-in exceptions for invalid input or failed operations;
- avoid swallowing worker, build, plugin, subprocess, or I/O errors.

Complex exercises may use helper modules, notebooks, C sources, or fixture
projects. `solution_00.py` remains the documented canonical entry point.

## Upstream Source Material

Missing book examples are resolved against:

`mastering-python/code_2@a012f6ce3f5bf11f5bf380d1c4e7f743355adb89`

Upstream code is example material, not a supported importable package. Solutions
must not clone or import it at runtime. Use SHA-pinned permalinks for provenance
and commit the smallest attributed local fixture or snippet needed for offline
execution. Preserve applicable MIT attribution.

## Exercise Coverage

Implementation is divided into 13 file-disjoint packets:

1. Chapter 2: five interactive Python exercises.
2. Chapters 4-5: six design-pattern and functional-programming exercises.
3. Chapter 6 exercises 1-4: tracking and memoization.
4. Chapter 6 exercises 5-7 and Chapter 7: descriptors, dispatch, validation,
   generators, and slicing.
5. Chapter 8: three metaclass exercises.
6. Chapters 9-10: three typing exercises and five testing/logging exercises.
7. Chapters 11-12: six debugging and performance exercises.
8. Chapter 13: two asyncio exercises.
9. Chapter 14 exercises 1-2: IPC and concurrent file processing.
10. Chapter 14 exercises 3-7: threaded/process traversal, worker pools, RPC,
    and parallel functional programming.
11. Chapters 15-16: Datashader, an interactive notebook, and deterministic NLP.
12. Chapter 17: two native-extension exercises.
13. Chapter 18: three packaging exercises.

Notable exercise decisions:

- Chapter 4's sorted collection must provide logarithmic insertion rather than
  merely logarithmic search followed by linear list insertion.
- Chapter 7 negative-step slicing may materialize a finite iterable and must
  document that requirement.
- Chapter 10's tox answer remains faithful to its flake8/mypy prompt even
  though repository-wide linting uses Ruff.
- Chapter 14 exercises 3 and 4 expose canonical threaded and multiprocessing
  APIs while preserving the historical specialized answer files.
- Chapter 14 exercise 5 must contain an actual persistent queue worker pool,
  replacing the current cross-reference-only answer.
- Chapter 15 uses tiny local data and a headlessly executable notebook.
- Chapter 16 uses deterministic local chapter-summary text and no downloaded
  NLP model.
- Chapter 17 exercise 1 implements and cross-checks ctypes, CFFI, and native
  extension `qsort` paths.
- Chapter 17 exercise 2 detects per-value conversion failures and cumulative
  overflow or underflow.
- Chapter 18 operates on temporary fixture packages and verifies build output.

## Tests

Every exercise has co-located pytest coverage derived from the exact prompt.
Tests cover:

- normal behavior;
- boundaries and empty inputs;
- invalid values and types;
- repeatability;
- failure propagation;
- representative plausible broken implementations.

Environment-heavy tests use focused integration rather than broad mocks:

- IPython, Jedi, widgets, and notebooks run headlessly.
- Pytest plugins use pytest's test-project facilities.
- Tox and packaging exercises use temporary fixture projects.
- Timing and memory utilities accept injectable clocks or samplers and use
  bounded tolerances.
- Concurrency tests use spawn-safe top-level callables, bounded pools, explicit
  timeouts, deterministic shutdown, loopback or local IPC only, and orphan
  checks.
- Native-extension tests compile in temporary build directories and cross-check
  results between implementations.

Tests must not require external network access, fixed ports, external datasets,
language-model downloads, or interactive input.

## Project and Dependency Configuration

Add a non-package uv project:

- `requires-python = ">=3.10"`
- `.python-version` set to `3.10`
- `[tool.uv] package = false`
- committed `uv.lock`

Dependency groups:

- `dev`: Ruff, pytest, pytest-timeout, mypy, Pyright, and Pyrefly
- `interactive`: IPython, Jedi, Colorama, and ipywidgets
- `scientific`: Datashader and headless notebook dependencies
- `nlp`: spaCy without an external model
- `native`: CFFI and native build tooling
- `packaging`: setuptools, build, wheel, and tox

The root must not define a build backend because automatic discovery could
accidentally package every chapter directory.

## Static Quality Gates

Ruff formats and lints:

- canonical `solution_00.py` files;
- co-located tests;
- canonical helper modules;
- package initializers.

Pyrefly, mypy, and Pyright check the same canonical scope in strict Python 3.10
mode. Exclude historical alternatives and intentionally invalid fixture
projects. Do not use repository-wide missing-import suppression. Untyped
third-party boundaries must use small typed adapters, protocols, or narrowly
documented error-code-specific suppressions.

## Lefthook

Add `lefthook.yml` with:

- pre-commit formatting and linting for relevant staged canonical Python files;
- safe re-staging of formatter/linter fixes;
- pre-push Pyrefly, mypy, Pyright, and complete pytest execution.

The root README documents:

```console
uv sync --all-groups
brew install lefthook
lefthook install
```

CI invokes the underlying quality commands directly rather than depending on
Lefthook.

## Continuous Integration

Add a GitHub Actions workflow with:

- read-only repository permissions;
- concurrency cancellation for superseded branch or pull-request runs;
- locked uv dependency installation and caching;
- explicit job timeouts.

Jobs:

1. Quality on Python 3.10:
   - `uv sync --locked --all-groups`
   - Ruff format check
   - Ruff lint
   - Pyrefly
   - mypy
   - Pyright
2. Pytest matrix on Python 3.10 and Python 3.14:
   - `uv sync --locked --all-groups`
   - complete pytest suite, including focused integration tests

Pin actions to reviewed commit SHAs. At design time the reviewed releases are:

- `actions/checkout` v7.0.1:
  `3d3c42e5aac5ba805825da76410c181273ba90b1`
- `astral-sh/setup-uv` v9.0.0:
  `c771a70e6277c0a99b617c7a806ffedaca235ff9`

## Team Workflow

The coordinator exclusively owns shared configuration, the lockfile, root
documentation, CI, and final integration. Up to three chapter agents work
concurrently with exclusive packet ownership.

Each chapter agent:

1. Reads the prompt and pinned upstream references.
2. Writes failing contract tests.
3. Implements or upgrades `solution_00.py`.
4. Adds the exercise README and attributed fixtures.
5. Runs packet-scoped Ruff, type checks, and pytest.
6. Reports verification evidence and unresolved ambiguity.

A separate reviewer checks prompt fidelity, Python 3.10 compatibility, public
API clarity, edge cases, test effectiveness, and README reproducibility.
Findings return to the owning agent before integration.

After every wave, the coordinator runs repository-wide canonical quality gates.
Agents must accommodate concurrent edits and never revert unrelated work.

## Acceptance Criteria

The work is complete only when:

- all 56 exercises have canonical answers and per-exercise READMEs;
- all exercise tests pass on Python 3.10 and Python 3.14;
- canonical scope has zero Ruff, Pyrefly, mypy, or Pyright findings;
- native, notebook, concurrency, pytest-plugin, tox, and packaging integration
  paths pass;
- setup and commands work from a clean locked environment;
- no runtime downloads, orphan processes, generated tracked artifacts, or
  unexplained skips remain;
- an independent final review has no unresolved findings.

Implementation remains local unless the user separately authorizes GitHub
writes.
