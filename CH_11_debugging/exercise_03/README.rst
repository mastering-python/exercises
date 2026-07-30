Exercise 3: line execution counts
=================================

Question
--------

.. code-block:: text

   3. Show how often that specific bit of code has been executed

Solution
--------

``count_executions`` uses the standard-library ``trace`` module to count line
events while running a generic callable. ``ExecutionCounts`` returns both the
callable's result and a line-number-to-frequency mapping. The public
``SourceLocation`` alias describes the filename and line-number keys produced
by ``trace`` before filtering.

Only events whose filename matches the callable's inspected source file appear
in the returned mapping. Lines executed in dependencies are excluded. A
callable without an inspectable source file is rejected before execution.
Callable exceptions propagate and no partial profile is returned.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run
---

Run the guarded demonstration:

.. code-block:: console

   $ uv run python -m CH_11_debugging.exercise_03.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest CH_11_debugging/exercise_03/test_solution_00.py -v

Historical source
-----------------

The immutable upstream references are
`T_02_selective_trace.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_11_debugging/T_02_selective_trace.py>`_
and
`T_03_filename_trace.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_11_debugging/T_03_filename_trace.py>`_.
The solution and tests are self-contained; no source files are copied from
those references.
