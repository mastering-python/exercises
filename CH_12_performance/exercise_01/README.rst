Exercise 1: memory-growth monitor
=================================

Question
--------

.. code-block:: text

   1. Try to create a decorator that monitors each run of a function and warns you if the memory usage grows each run.

Solution
--------

``MemoryGrowthMonitor`` is a callable wrapper, and
``monitor_memory_growth`` constructs it as a decorator. The wrapped callable
runs before the injected sampler. Only a successful call consumes a sample,
and only growth above the nonnegative byte tolerance emits
``ResourceWarning``. Decreases, unchanged samples, and growth equal to the
tolerance do not warn. If sampling fails, the prior successful sample remains
the comparison baseline.

The wrapper is descriptor-aware, so it also decorates instance methods while
preserving their metadata, ``__wrapped__`` reference, and inspectable
signature. The class attribute owns one monitor: calls through every instance
share its previous-sample baseline. Access through the class returns that
monitor object.

The default sampler starts ``tracemalloc`` when needed and reads its current
traced allocation count. That sample describes traced Python allocations, not
whole-process resident memory. Tests inject integer samples and make no
assumptions about real memory usage.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run
---

Run the guarded demonstration:

.. code-block:: console

   $ uv run python -m CH_12_performance.exercise_01.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest CH_12_performance/exercise_01/test_solution_00.py -v

Historical source
-----------------

The immutable upstream references are
`T_11_tracemalloc.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_12_performance/T_11_tracemalloc.py>`_,
`T_12_memory_profiler.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_12_performance/T_12_memory_profiler.py>`_,
and
`T_13_memory_leaks.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_12_performance/T_13_memory_leaks.py>`_.
The solution and tests are self-contained; no source files are copied from
those references.
