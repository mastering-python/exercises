Exercise 1: execution timing
============================

Question
--------

1. Extend the `track` function to monitor execution time.

Solution
--------

``track`` supports both ``@track`` and a configured
``@track(label=..., clock=..., reporter=...)`` form. Each call produces a
frozen ``Timing`` value containing its label, elapsed seconds, and failure
state.

The clock and reporter are injectable. A deterministic clock makes elapsed
time straightforward to test, while a custom reporter can store or publish
timings without changing the decorator. The default clock is
``time.perf_counter`` and the default reporter prints the result.

Timing is recorded in a ``finally`` block. Successful calls report
``failed=False``; calls that raise report ``failed=True`` before the original
exception continues to the caller.

Dependencies
------------

The solution has no third-party runtime dependencies and requires Python 3.10
or newer. Tests use the repository's ``pytest`` development dependency.

Run the guarded demonstration:

.. code-block:: console

   uv run python -m CH_06_decorators.exercise_01.solution_00

Run the focused tests:

.. code-block:: console

   uv run pytest CH_06_decorators/exercise_01/test_solution_00.py

Reference
---------

The decorator follows the chapter's `chaining decorators example
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_03_chaining_decorators.rst>`_.
