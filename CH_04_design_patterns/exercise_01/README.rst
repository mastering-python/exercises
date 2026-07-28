Sorted dictionary
=================

Question
--------

Create SortedDict collection takes keyfunc decide sort order.

Answer
------

``SortedDict`` implements ``collections.abc.MutableMapping`` using an ordinary
dictionary for storage.  Its optional ``keyfunc`` receives each key, not its
value.  Iteration sorts the current keys, so insertions, replacements, and
deletions are reflected immediately without maintaining a second index.
Consequently, each iteration costs O(n log n).

No upstream substrate was needed for this answer.

Dependencies
------------

The answer requires Python 3.10 or newer and uses only the standard library.
The focused test requires pytest from the repository's ``dev`` dependency
group.

Run
---

From the repository root:

.. code-block:: console

   $ uv run python CH_04_design_patterns/exercise_01/solution_00.py
   $ uv run pytest CH_04_design_patterns/exercise_01/test_solution_00.py
