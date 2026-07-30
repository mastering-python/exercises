Exercise 2
==========

Question
--------

.. code-block:: text

    2. Extend the `track` function with min/max/average execution time and call count.

Solution
--------

``track`` supports a bare decorator (``@track``), a configured decorator
(``@track(label=..., clock=..., reporter=...)``), and a configured direct call
(``track(function, label=..., clock=..., reporter=...)``).  Each decorated
function has its own mutable ``TimingStats`` instance at ``function.stats`` and
a zero-argument ``function.print_stats()`` method.  The aggregates use seconds:

An explicit ``label`` always wins. Otherwise, the default label is a string
``function.__name__`` when available, or ``type(function).__name__`` for
callables such as ``functools.partial`` instances.

* ``count`` is the number of calls with a completed duration.
* ``total`` is the sum of those durations.
* ``minimum`` and ``maximum`` are the shortest and longest durations.
* ``average`` is ``total / count``.

A failed target call is included when the ending clock succeeds.  Empty
statistics have ``minimum``, ``maximum``, and ``average`` set to ``None``.
``print_stats()`` renders them as ``n/a`` and renders every duration in seconds
to six decimal places.  Its exact empty output is:

.. code-block:: text

   lookup stats: count=0, total=0.000000s, minimum=n/a, maximum=n/a, average=n/a

The clock and reporter are injectable.  Tests use deterministic clock values;
they do not sleep.  A starting-clock failure prevents the target call.  An
ending-clock failure produces no duration or statistics.  After a successful
target call, ending-clock and reporter failures propagate.  After a target
failure, instrumentation is attempted, but an ending-clock or reporter failure
cannot replace the original target exception.  A completed duration updates
statistics before exactly one ``Timing`` is sent to the reporter.

Dependencies
------------

The solution uses only the Python standard library and requires Python 3.10 or
newer.  Tests use the repository's ``pytest`` development dependency.

Run the deterministic, guarded demonstration:

.. code-block:: console

   uv run python -m CH_06_decorators.exercise_02.solution_00

Run the focused tests:

.. code-block:: console

   uv run pytest -W error CH_06_decorators/exercise_02 -v

Reference
---------

The decorator extends the chapter's `chaining decorators example
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_03_chaining_decorators.rst>`_.
