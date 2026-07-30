Exercise 1: iterable slicing with negative steps
================================================

Question
--------

1. Create a generator similar to `itertools.islice()` that allows for a negative step so you can execute `some_list[20:10:-1]`.

Solution
--------

``islice(iterable, start, stop, step=1)`` returns an iterator. It first
normalizes all three slice arguments through ``operator.index`` without
touching the source. Integer-compatible objects are accepted, while floats and
other invalid indices raise ``TypeError`` immediately.

For a positive ``step``, the function delegates directly to
``itertools.islice``. The source remains streaming and lazy: values are
consumed only as the result requests them, and the standard library's
restrictions on negative bounds still apply.

A zero ``step`` raises ``ValueError`` immediately. For a negative ``step``, the
function materializes the source exactly once, applies an ordinary list slice,
and returns an iterator over that result. This provides list-slice behavior for
negative bounds, out-of-range bounds, empty slices, and step magnitudes greater
than one.

Materialization means negative-step slicing requires a finite iterable and uses
:math:`O(n)` temporary memory. Calling it with an infinite iterable never
terminates. Positive-step slicing does not have this limitation.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest and the static
analysis tools.

Run
---

Run the guarded module demonstration from the repository root:

.. code-block:: console

   $ uv run python -m CH_07_generators_and_coroutines.exercise_01.solution_00

Run the focused tests with warnings treated as errors:

.. code-block:: console

   $ uv run pytest -W error CH_07_generators_and_coroutines/exercise_01/test_solution_00.py

Reference
---------

The chapter's original iterable-slicing discussion is preserved in the pinned
`T_07_islice.rst source
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_07_generators_and_coroutines/T_07_islice.rst>`_.
