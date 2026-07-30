Exercise 3: static legacy-project migration
===========================================

Question
--------

.. code-block:: text

   3. Try and convert existing projects from `setup.py` to a `pyproject.toml` structure

Answer
------

``read_setup_metadata`` parses the legacy file as an abstract syntax tree; it
never imports or executes ``setup.py``. The accepted static subset contains one
setup call with literal ``name``, ``version``, ``description``,
``python_requires``, and ``entry_points`` fields. Keyword expansion, dynamic
supported fields, duplicate setup calls or console-script names, and malformed
``name=module:function`` entries are rejected.

``migrate_project`` leaves the source unchanged and creates a deterministic
``src``-layout project in a new destination. It copies only the package and
README, renders safely quoted modern metadata, and never copies ``setup.py``.
Distribution names are validated and must resolve to exactly one package child
beneath the source. Source and destination paths cannot contain each other.
Migration stages the complete output in a sibling temporary directory, removes
that directory after any failure, and publishes only through a final rename.
``setup.py``, the README, the package root, and every package descendant must
not be symlinks. A no-follow recursive validation rejects file and directory
links before any destination or temporary migration directory is created.

Security and dependencies
-------------------------

Python 3.10 or newer is required. The repository's ``packaging`` dependency
group supplies setuptools, build, and wheel. Tests copy the committed legacy
fixture into pytest temporary storage, build with ``python -m build
--no-isolation``, require exactly one wheel and one source distribution, inspect
their metadata and contents, and smoke-test the wheel import and console target.
All subprocesses use captured output and timeouts. No setup code executes during
metadata extraction, no build artifact enters the repository, and no network
access is required.

Run
---

Run the focused tests from the repository root:

.. code-block:: console

   $ uv run --group packaging pytest CH_18_packaging/exercise_03/test_solution_00.py -vv

References and provenance
-------------------------

The implementation is informed by the chapter's immutable
`basic setup.py example
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_18_packaging/T_02_basic_setup_py/setup.py>`_
and
`basic pyproject.toml example
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_18_packaging/T_00_basic_pyproject/pyproject.toml>`_.
The upstream material is MIT licensed; this exercise solution and fixture are
self-contained.
