Exercise 3: memoizing container arguments
=========================================

Question
--------

The relevant chapter exercise-list excerpt is:

1. Extend the `track` function to monitor execution time.
2. Extend the `track` function with min/max/average execution time and call count.
3. Modify the memoization function to function with unhashable types.

Solution
--------

``memoize`` freezes arguments into immutable, type-tagged cache keys.  It
supports arbitrarily nested tuples, lists, dictionaries, sets, and frozen
sets.  Lists remain distinct from tuples, sets remain distinct from frozen
sets, and scalar runtime types remain distinct, including ``bool`` and
``int``.

Dictionary and set order does not affect a key.  Both dictionary keys and
values are frozen recursively.  Shared references are accepted when they do
not form a cycle.  Active recursion cycles raise ``ValueError("cyclic
argument")``.  Other unhashable objects raise ``TypeError`` naming the
unsupported type.

The module-level ``cache`` lives for the lifetime of the Python process.
Every decoration receives a unique opaque namespace in its cache keys, so
distinct functions and callable objects cannot reuse one another's results.
Keyword argument order does not affect a key.  ``None`` is a normal cached
result.  A call that raises an exception is not cached and will run again on
the next call.

Running
-------

Run the solution module:

.. code-block:: console

   uv run python -m CH_06_decorators.exercise_03.solution_00

Run the exercise tests:

.. code-block:: console

   uv run pytest -W error CH_06_decorators/exercise_03 -v

Reference
---------

The solution extends the chapter's `memoization example
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_05_memoization.rst>`_.
