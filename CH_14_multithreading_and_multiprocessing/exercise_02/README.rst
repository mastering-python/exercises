Exercise 2: threaded directory sizes
====================================

Question
--------

The original exercise question is:

.. code-block:: text

   2. Read all files in a directory and sum the size of the files by reading each file using `concurrent.futures`. If you want an extra challenge, walk through the directories recursively by letting the thread/process queue new items while running.

Solution
--------

``get_size(path)`` returns one file's byte size. ``get_total_size(path)`` sums
only immediate non-symlink regular files.
``get_total_size_recursive(path)`` discovers nested entries iteratively and
sums non-symlink regular files without following file or directory symlinks.
Both aggregators reject non-directories, symlink roots, and non-positive worker
counts. Empty directories return zero.

Both aggregators keep a pinned, no-follow root descriptor through worker
completion and bound submitted file work to the effective worker count.
Recursive discovery uses deterministic depth-first order. Each queued
directory is reopened securely from the root with short-lived descriptors. A
``ThreadPoolExecutor`` runs ``get_size`` for descriptor-backed paths. Results
are read through each ``Future.result()``, so worker exceptions propagate to
the caller. ``main(path)`` prints the flat and recursive totals.

Dependencies
------------

The solution uses only the Python 3.10 standard library. Tests use the
repository's ``pytest`` development dependency.

Run the guarded demonstration:

.. code-block:: console

   uv run python -m CH_14_multithreading_and_multiprocessing.exercise_02.solution_00

Run the focused tests:

.. code-block:: console

   uv run pytest CH_14_multithreading_and_multiprocessing/exercise_02/test_solution_00.py -vv

Reference
---------

The implementation builds on the chapter's immutable
`concurrent futures example
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_00_concurrent_futures.py>`_
and
`thread batch-processing example
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_07_thread_batch_processing.py>`_.
The upstream material is MIT licensed; this solution is self-contained.
