Exercise 2: runtime-deviation monitor
=====================================

Question
--------

.. code-block:: text

   2. Try to create a decorator that monitors the runtime of a function and warns you if it deviates too much from the previous run. Optionally, you could make the function generate a (running) average runtime as well.

Solution
--------

``RuntimeMonitor`` is a callable wrapper, and ``monitor_runtime`` constructs
it as a decorator. Each successful duration is compared with the running
average from earlier successful calls. A relative difference above the
nonnegative ``max_deviation`` emits ``RuntimeWarning``. No comparison is made
until a positive prior average exists.

The wrapper is descriptor-aware, so it also decorates instance methods while
preserving their metadata, ``__wrapped__`` reference, and inspectable
signature. The class attribute owns one monitor, and calls through every
instance contribute to that monitor's shared statistics. Both class access and
a bound instance method expose the same current ``stats`` value.

The frozen ``RuntimeStats`` value exposes successful call count, total
seconds, and the derived average. Failed callables propagate without taking an
end-clock sample or changing statistics. A clock that moves backwards raises
``ValueError`` and also leaves statistics unchanged. Tests inject clock values
and make no assumptions about machine speed.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run
---

Run the guarded demonstration:

.. code-block:: console

   $ uv run python -m CH_12_performance.exercise_02.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest CH_12_performance/exercise_02/test_solution_00.py -v

Historical source
-----------------

The immutable upstream references are
`T_00_timeit.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_12_performance/T_00_timeit.py>`_
and
`T_06_selective_profiling.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_12_performance/T_06_selective_profiling.py>`_.
The solution and tests are self-contained; no source files are copied from
those references.
