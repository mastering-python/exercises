Exercise 3: type hint recursive trees
=======================================

Question
--------

The relevant chapter exercise-list excerpt is:

.. code-block:: text

   1. Type hint complex `dict`
   2. Type hint nested types
   3. Type hint recursive types

Solution
--------

``Tree`` names the recursive ``dict[str, "Tree"]`` shape. Each mapping key
names one node and its value contains that node's children. The root mapping is
the container for those named nodes, so it is not itself counted.
``count_nodes`` therefore adds one for every mapping entry and includes the
entry's child-tree count. Dictionary insertion order and node names do not
affect the result, and the input is never modified.

The traversal uses an explicit post-order stack, so a valid tree may be deeper
than Python's recursion limit. Cycle detection tracks dictionary identities
only along the active path. Revisiting an active dictionary raises exactly
``ValueError("tree contains cycle")``.

After a subtree is completed, its count is memoized by dictionary identity.
Each unique dictionary is traversed once, while every parent reference still
adds one plus the cached child count. Shared acyclic directed graphs therefore
remain valid and are counted once per occurrence, including compact graphs
whose expanded counts are very large. This teaching function relies on the
type annotation and performs no additional runtime shape validation.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for tests.

Run
---

Run the guarded canonical demonstration from the repository root:

.. code-block:: console

   $ uv run python -m CH_09_documentation.exercise_03.solution_00

Run focused tests with warnings treated as errors:

.. code-block:: console

   $ uv run pytest -W error CH_09_documentation/exercise_03/test_solution_00.py

Historical source
-----------------

The chapter's type-hinting discussion is preserved in
`T_00_type_hinting.rst <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_09_documentation/T_00_type_hinting.rst>`_.
