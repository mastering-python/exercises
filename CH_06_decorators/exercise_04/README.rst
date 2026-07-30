Exercise 4: per-function memoization
====================================

Question
--------

The relevant chapter exercise-list excerpt is:

1. Extend the `track` function to monitor execution time.
2. Extend the `track` function with min/max/average execution time and call
   count.
3. Modify the memoization function to function with unhashable types.
4. Modify the memoization function to have a cache per function instead of a global one.

Solution
--------

``memoize`` gives every decoration its own closure-local cache. Two decorated
functions therefore never share entries, even when called with the same
arguments. Each wrapper exposes its actual live ``cache`` dictionary for
inspection and a ``cache_clear()`` method that clears only that wrapper.

The cache key freezes positional and keyword arguments with Exercise 3's
freezer. Lists, tuples, dictionaries, sets, and frozen sets may be nested.
Dictionary and set order does not affect a key, while container types and
scalar runtime types remain distinct. For example, a list differs from a tuple,
a set differs from a frozen set, and ``bool`` differs from ``int``.

Active recursion cycles raise ``ValueError("cyclic argument")``. Other
unsupported unhashable objects raise ``TypeError``. Shared references that do
not form a cycle remain valid.

A private missing-value sentinel allows ``None`` to be cached. The wrapped
callable runs only on a cache miss, and a result is stored only after a
successful return, so exceptions are never cached. ``functools.wraps``
preserves ordinary metadata, custom attributes, ``__wrapped__``, and the
inspectable signature.

Running
-------

Run the solution module:

.. code-block:: console

   uv run python -m CH_06_decorators.exercise_04.solution_00

Run the exercise tests:

.. code-block:: console

   uv run pytest -W error CH_06_decorators/exercise_04 -v

Reference
---------

This solution extends the chapter's
`memoization example <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_05_memoization.rst>`_.
