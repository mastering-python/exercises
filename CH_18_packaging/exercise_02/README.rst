Exercise 2: interactive version command
=======================================

Question
--------

.. code-block:: text

   2. Extend the version bumping command by interactively asking for a major, minor, or patch upgrade

Answer
------

``choose_version_part`` accepts ``major``, ``minor``, and ``patch`` without
case sensitivity, plus the numeric aliases ``1``, ``2``, and ``3``. Invalid
input raises ``ValueError`` instead of silently choosing a version component.
Its input function is injectable for deterministic direct tests.

``InteractiveBumpVersion`` inherits the non-interactive command. It prompts by
default, including through subprocess standard input, while an explicit
``--part`` bypasses prompting for automation.

Security and dependencies
-------------------------

Python 3.10 or newer is required. The repository's ``packaging`` dependency
group supplies setuptools and the test tools. Subprocess tests use copied
temporary fixture projects, the active Python interpreter, captured output, and
timeouts. They neither modify the repository nor require network access.

Run
---

Run the focused tests from the repository root:

.. code-block:: console

   $ uv run --group packaging pytest CH_18_packaging/exercise_02/test_solution_00.py -vv

Reference and provenance
------------------------

The implementation is informed by the chapter's immutable
`basic setup.py example
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_18_packaging/T_02_basic_setup_py/setup.py>`_.
The upstream material is MIT licensed; this exercise solution is self-contained.
