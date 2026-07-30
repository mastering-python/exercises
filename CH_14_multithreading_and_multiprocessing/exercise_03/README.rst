Exercise 3: threaded and process file sizes
===========================================

Question
--------

The original exercise question is:

.. code-block:: text

    3. Read all files in a directory and sum the size of the files by reading each file using `threading` and `multiprocessing`.

Solution
--------

``threaded_total_size(path)`` uses persistent raw threads and
``multiprocessing_total_size(path)`` uses a bounded spawn-process pool. Both
sum the immediate regular, non-symlink files in deterministic name order.
They reject invalid directories and worker counts, return zero for an empty
directory, and propagate worker errors.

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

    uv run python -m CH_14_multithreading_and_multiprocessing.exercise_03.solution_00

Run the focused tests:

.. code-block:: console

    uv run pytest CH_14_multithreading_and_multiprocessing/exercise_03/test_solution_00.py -vv

References
----------

The implementation builds on the chapter's immutable
`thread batch-processing example <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_07_thread_batch_processing.py>`_
and
`process batch-processing example <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_08_process_batch_processing.py>`_.
The upstream material is MIT licensed; this solution is self-contained.
