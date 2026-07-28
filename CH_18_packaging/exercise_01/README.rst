Exercise 1: setuptools version command
======================================

Question
--------

.. code-block:: text

   1. Create a `setuptools` command to bump the version in your package

Answer
------

``bump_version`` accepts strict three-integer semantic versions and increments
the selected major, minor, or patch component. Major and minor bumps reset
lower-order components. ``read_version`` and ``write_version`` require exactly
one ``__version__`` assignment and preserve every other byte of the module.

``BumpVersion`` exposes ``--version-file`` and ``--part`` setuptools command
options. The part defaults to ``patch``. Finalization rejects missing files and
unknown parts before execution; execution writes only the designated version
file.

Security and dependencies
-------------------------

Python 3.10 or newer is required. The repository's ``packaging`` dependency
group supplies setuptools and the test/build tools. Tests create disposable
fixture projects, invoke their commands with the active Python interpreter, and
use bounded subprocesses with captured output. No repository metadata file or
network service is modified.

Run
---

Run the focused tests from the repository root:

.. code-block:: console

   $ uv run --group packaging pytest CH_18_packaging/exercise_01/test_solution_00.py -vv

Reference and provenance
------------------------

The implementation is informed by the chapter's immutable
`basic setup.py example
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_18_packaging/T_02_basic_setup_py/setup.py>`_.
The upstream material is MIT licensed; this exercise solution is self-contained.
