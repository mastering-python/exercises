Exercise 2: execution duration
==============================

Question
--------

.. code-block:: text

   2. Measure the duration of the execution

Solution
--------

``CallTimer.measure`` runs one generic callable and returns a frozen
``TimedResult`` containing its value and elapsed seconds. Its default
``time.perf_counter`` clock is monotonic. Callers can inject another clock,
which makes tests deterministic without assumptions about machine speed.
``measure_call`` is the convenience API for the default clock.

The start sample is taken before the callable. The end sample is taken only
after a successful return, so callable exceptions propagate without requiring
another clock value. A successful callable followed by an end sample earlier
than its start raises ``ValueError`` rather than reporting a negative duration.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run
---

Run the guarded demonstration:

.. code-block:: console

   $ uv run python -m CH_11_debugging.exercise_02.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest CH_11_debugging/exercise_02/test_solution_00.py -v

Historical source
-----------------

Selective instrumentation is illustrated by the immutable upstream
`T_02_selective_trace.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_11_debugging/T_02_selective_trace.py>`_.
The solution and tests are self-contained; no source files are copied from
that reference.
