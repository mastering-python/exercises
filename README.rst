Mastering Python Second Edition Exercises
=========================================

This repository contains solutions for the exercises in *Mastering Python,
Second Edition*. Each ``solution_00.py`` is the maintained, typed reference
solution. Higher-numbered ``solution_NN.py`` files and specialized solution
files are community alternatives.

Requirements
------------

Development requires Python 3.10 or newer, uv, and Lefthook. On macOS, install
the tools, synchronize every dependency group, and install the Git hooks:

.. code-block:: console

   $ brew install uv lefthook
   $ uv sync --all-groups
   $ lefthook install

Running exercises
-----------------

Each ``exercise_NN`` directory contains its exact question, a concise
explanation, the canonical answer in ``solution_00.py``, its dependencies, and
focused tests. Run an answer or its tests from the repository root. For
example:

.. code-block:: console

   $ uv run python CH_04_design_patterns/exercise_01/solution_00.py
   $ uv run pytest CH_04_design_patterns/exercise_01/test_solution_00.py

Run all checks
--------------

Run the complete formatting, linting, type-checking, and test suite before
submitting changes:

.. code-block:: console

   $ uv run ruff format --check .
   $ uv run ruff check .
   $ uv run pyrefly check
   $ uv run mypy .
   $ uv run pyright
   $ uv run pytest

Dependency groups
-----------------

The lockfile contains separate dependency groups so an exercise can use only
the tools it needs:

``dev``
   Documentation rendering, formatting, linting, type-checking, and tests.
``interactive``
   Interactive Python, widgets, terminal colors, and completion support.
``scientific``
   Numerical, tabular, notebook, and visualization tools.
``nlp``
   Natural-language processing and its command-line support.
``native``
   Native-extension build tools and C foreign-function interfaces.
``packaging``
   Distribution builds, wheels, and isolated environment testing.

After the package cache has been populated, reproduce the complete locked
environment without network access:

.. code-block:: console

   $ uv sync --all-groups --locked --offline

Contributing
------------

Alternative solutions are welcome and use the next available
``solution_NN.py``. Keep canonical files, tests, and exercise documentation
unchanged unless correcting the reference answer. All submitted Python code
must be formatted, linted, typed, and tested. The repository-wide commands
above validate the maintained canonical scope.
