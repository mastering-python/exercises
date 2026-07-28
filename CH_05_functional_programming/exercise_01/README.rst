Exercise 1: quicksort
=====================

Question
--------

Implement the quicksort algorithm.

Solution
--------

``quicksort`` accepts any iterable and returns a fresh sorted list. It
materializes the iterable once and never mutates the iterable, an input list,
or the objects contained in it. Empty and singleton inputs also produce fresh
lists. The ``qs`` name remains available as a typed compatibility wrapper.

The implementation deterministically chooses the first item as the pivot.
Each remaining item is compared with the pivot once using only ``<``. Items
that compare less than the pivot enter the lower partition; all other items
enter the upper partition. This retains duplicates and distinct objects that
are equivalent under the ordering.

Values must provide a strict weak ordering through ``<``: comparisons should
be irreflexive and transitive, and equivalence induced by neither value being
less than the other should also be transitive. Comparison exceptions propagate
to the caller.

Average time complexity is :math:`O(n \log n)` with :math:`O(n)` partition
storage across one recursion level. Choosing the first pivot intentionally
makes already sorted, reverse-sorted, and all-equivalent inputs worst-case
:math:`O(n^2)` time with :math:`O(n)` recursion depth. Large adversarial inputs
can therefore reach Python's recursion limit; the deterministic recursive form
is retained to demonstrate the functional algorithm rather than avoid that
tradeoff.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest and the static
analysis tools.

Run the guarded module demonstration:

.. code-block:: console

   $ uv run python -m CH_05_functional_programming.exercise_01.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest -W error CH_05_functional_programming/exercise_01/test_solution_00.py

Historical alternative
----------------------

``solution_01.py`` is preserved byte-for-byte as the historical in-place
partitioning alternative. Unlike the primary functional solution, it mutates
the caller's list and requires a sequence with index access.
