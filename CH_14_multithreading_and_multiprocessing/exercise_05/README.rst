Exercise 5: persistent process workers
======================================

Question
--------

The original exercise question is:

.. code-block:: text

    5. Create a pool of workers that keeps waiting for items to be queued through `multiprocessing.Queue()`.

Solution
--------

``PersistentWorkerPool`` starts a fixed set of spawn-process workers for one
top-level callable. ``submit()``, ``result()``, and ``map()`` exchange frozen
``Task``, ``Success``, and ``Failure`` messages through multiprocessing
queues. Worker PIDs stay stable across calls, results preserve input order,
and out-of-order replies are cached by task identifier. Worker exceptions
cross the process boundary as ``WorkerError``. ``close()`` and the context
manager perform idempotent, bounded cooperative shutdown.

``square()`` is the spawn-picklable demonstration function.

Dependencies
------------

The solution has no third-party runtime dependencies and uses only the Python
3.10 standard library. Tests use the repository's ``pytest`` development
dependency.

Run the guarded demonstration:

.. code-block:: console

    uv run python -m CH_14_multithreading_and_multiprocessing.exercise_05.solution_00

Run the focused tests:

.. code-block:: console

    uv run pytest CH_14_multithreading_and_multiprocessing/exercise_05/test_solution_00.py -vv

References
----------

The implementation builds on the chapter's immutable
`thread batch-processing example <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_07_thread_batch_processing.py>`_,
`process batch-processing example <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_08_process_batch_processing.py>`_,
and
`multiprocessing pool example <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_09_multiprocessing_pool.py>`_.
The upstream material is MIT licensed; this solution is self-contained.
