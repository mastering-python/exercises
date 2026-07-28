Sorted list
===========

Question
--------

Create a SortedList collection that has O(log(n)) inserts and always returns a sorted list during each iteration.

Answer
------

``SortedList`` implements ``collections.abc.Collection`` with a deterministic
AVL tree. Each node stores one representative value and its sort key. Values
with the same sort key remain in an insertion-ordered duplicate bucket, so
equal keys do not disappear or reorder.

AVL rotations keep the tree height logarithmic, including already sorted input.
``add`` and its ``insert`` alias therefore take O(log n) sort-key comparisons.
``len`` and the read-only ``tree_height`` diagnostic take O(1) time. Iteration
visits each stored value once in sort-key order and takes O(n) time. Membership
uses O(log n) key comparisons to reach one matching-key bucket, then compares
only values in that bucket; its worst case includes the bucket size.

The constructor accepts any iterable and an optional keyword-only ``key``
function. Without ``key``, values themselves provide the ordering. Public
operations are ``add``, ``insert``, ``len``, iteration, membership, ``repr``,
and ``tree_height``.

Values returned by ``key`` must form a strict weak ordering under ``<``. In
particular, the ordering must be irreflexive and transitive, and
incomparability must be transitive. Incomparable values such as floating-point
NaN do not satisfy this contract, so the collection does not promise correct
ordering for them.

Membership applies the configured ``key`` function to its candidate. The
candidate must therefore be accepted by that function, and its result must be
comparable with the stored sort keys. A foreign candidate may raise the
original key-function or comparison error; ``SortedList`` intentionally does
not hide it.

The book's bisect discussion is available in the immutable upstream reference:
https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_04_design_patterns/T_10_bisect.rst

Dependencies
------------

The answer requires Python 3.10 or newer and uses only the standard library.
The focused test requires pytest from the repository's ``dev`` dependency
group.

Run
---

From the repository root:

.. code-block:: console

   $ uv run python CH_04_design_patterns/exercise_02/solution_00.py
   $ uv run pytest -W error CH_04_design_patterns/exercise_02/test_solution_00.py
