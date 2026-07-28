Exercise 3: reusable groupby lists
==================================

Question
--------

Write a groupby function that returns lists of results instead of generators.

Solution
--------

``groupby`` accepts an iterable first and an optional ``key`` function second.
When ``key`` is omitted or ``None``, each hashable item is its own group key.
When a key function is supplied, its hashable result is the group key, so input
items themselves may be unhashable.

This differs from Exercise 2, whose API is function-first:
``groupby(func, seq)``.  It also differs from ``itertools.groupby``.
``itertools.groupby`` returns lazy group iterators and starts a new group when
the key changes, so equal non-adjacent keys form separate groups unless the
input is suitably ordered.  This solution makes one dictionary entry per equal
key regardless of adjacency and stores each group in a concrete, reusable
``list``.

The result preserves first key encounter order, and every group preserves item
encounter order.  The input is traversed once without sorting.  An input
iterator is therefore consumed, and the key callback is called exactly once per
item in encounter order.  Callback exceptions and errors from unhashable group
keys propagate immediately.  A non-callable, non-``None`` key raises
``TypeError`` before the iterable is consumed.

Concrete lists can be traversed repeatedly and mutated independently after the
call.  The tradeoff is eager storage: grouping uses :math:`O(n)` output memory,
whereas ``itertools.groupby`` can expose each adjacent group lazily.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest and the static
analysis tools.

Run
---

Run the guarded module demonstration from the repository root:

.. code-block:: console

   $ uv run python -m CH_05_functional_programming.exercise_03.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest -W error CH_05_functional_programming/exercise_03/test_solution_00.py

Reference
---------

The chapter's original discussion is preserved in the pinned
`T_14_groupby.rst source
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_05_functional_programming/T_14_groupby.rst>`_.
