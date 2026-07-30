Exercise 2: sorting-independent groupby
========================================

Question
--------

Write a groupby function that isn’t affected by sorting.

Solution
--------

``groupby`` accepts a key function and any iterable. It returns a dictionary
whose keys are the key function's results and whose values are lists of the
matching input items.

Unlike ``itertools.groupby``, which starts a new group whenever the key
changes, this implementation combines equal keys even when their items are not
consecutive. Pre-sorting can make equal keys adjacent for
``itertools.groupby``, but it changes encounter order and generally
requires materializing the iterable. This implementation does neither.

Dictionary keys retain first-key encounter order. Each group's list retains
the encounter order of its items. The iterable is consumed once, the key
function is called exactly once per item, and the input container is not
structurally modified.

Assuming average constant-time dictionary operations, the algorithm takes
:math:`O(n)` time and :math:`O(n)` output space. It does not sort or
materialize the complete input before grouping. Passing an iterator consumes
it. Key-function side effects occur in item encounter order, and callback
exceptions propagate immediately. Keys must be hashable; an unhashable runtime
key raises ``TypeError``.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest and the static
analysis tools.

Run the guarded module demonstration:

.. code-block:: console

   $ uv run python -m CH_05_functional_programming.exercise_02.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest -W error CH_05_functional_programming/exercise_02/test_solution_00.py

Reference
---------

The chapter's original discussion is preserved at
https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_05_functional_programming/T_14_groupby.rst.
