Exercise 7: bounded parallel merge sort
=======================================

Question
--------

The original exercise question is:

.. code-block:: text

    7. Apply your functional skills to calculate something in a parallel way. Perhaps parallel sorting?

Solution
--------

``merge()``, ``split()``, and ``merge_sort()`` provide deterministic,
non-mutating sequential building blocks. ``parallel_merge_sort()`` validates
integer-only input, creates at most one non-empty chunk per input value, and
uses no more processes than the requested bound or input length. Spawn is the
default process context. Sorted chunks are merged in deterministic balanced
rounds. Empty input returns without starting a worker.
``multiprocessing_merge_sort()`` is the compatibility wrapper.

Dependencies
------------

The solution has no third-party runtime dependencies and uses only the Python
3.10 standard library. Tests use the repository's ``pytest`` development
dependency.

Run the guarded demonstration:

.. code-block:: console

    uv run python -m CH_14_multithreading_and_multiprocessing.exercise_07.solution_00

Run the focused tests:

.. code-block:: console

    uv run pytest CH_14_multithreading_and_multiprocessing/exercise_07/test_solution_00.py -vv

References
----------

The implementation builds on the chapter's immutable
`multiprocessing pool example <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_09_multiprocessing_pool.py>`_.
The upstream material is MIT licensed; this solution is self-contained.
