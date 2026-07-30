Exercise 4: recursive worker queues
===================================

Question
--------

The original exercise question is:

.. code-block:: text

    4. As above, walk through the directories recursively by letting the thread/process queue new items while running.

Solution
--------

``threaded_recursive_size(path)`` and
``multiprocessing_recursive_size(path)`` keep persistent workers alive while
the traversal grows. Workers discover sorted child directories and return
``ScanResult`` messages; the parent-owned scheduler queues those children and
tracks the exact outstanding count. Non-symlink regular files are counted,
directory symlinks are not followed, and ``ScanFailure`` becomes a
``WorkerScanError`` instead of disappearing across the worker boundary.
Concurrent failures are exposed in deterministic directory order through
``WorkerScanError.failures``. Timeouts bound scheduling and cleanup.

The historical ``threading_solution_00.py`` and
``multiprocessing_solution_00.py`` files remain available as specialized
alternatives.

Dependencies
------------

The solution has no third-party runtime dependencies and uses only the Python
3.10 standard library. Tests use the repository's ``pytest`` development
dependency.

Run the guarded demonstration:

.. code-block:: console

    uv run python -m CH_14_multithreading_and_multiprocessing.exercise_04.solution_00

Run the focused tests:

.. code-block:: console

    uv run pytest CH_14_multithreading_and_multiprocessing/exercise_04/test_solution_00.py -vv

References
----------

The implementation builds on the chapter's immutable
`thread batch-processing example <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_07_thread_batch_processing.py>`_
and
`process batch-processing example <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_08_process_batch_processing.py>`_.
The upstream material is MIT licensed; this solution is self-contained.
