Exercise 6: allowlisted queue RPC
=================================

Question
--------

The original exercise question is:

.. code-block:: text

    6. Convert the pool above into a safe RPC (remote procedure call) type of operation.

Solution
--------

``RpcWorkerPool.call()`` exchanges frozen, identified request and reply
messages with persistent spawn-process workers. ``RPC_METHODS`` is an
immutable allowlist containing only ``add`` and ``repeat``. Workers never
evaluate code, import client-selected modules, dispatch arbitrary attributes,
or accept client-supplied callables. Unknown names raise
``UnknownMethodError``; exceptions from an allowlisted method raise
``RemoteCallError``. Either failure leaves the worker available for later
requests. Shutdown is cooperative, idempotent, and bounded.

Dependencies
------------

The solution has no third-party runtime dependencies and uses only the Python
3.10 standard library. Tests use the repository's ``pytest`` development
dependency.

Run the guarded demonstration:

.. code-block:: console

    uv run python -m CH_14_multithreading_and_multiprocessing.exercise_06.solution_00

Run the focused tests:

.. code-block:: console

    uv run pytest CH_14_multithreading_and_multiprocessing/exercise_06/test_solution_00.py -vv

References
----------

The implementation draws on the chapter's immutable remote-multiprocessing
`server example <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_17_remote_multiprocessing/server.py>`_
and
`function registry <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_17_remote_multiprocessing/functions.py>`_.
The upstream material is MIT licensed; this solution is self-contained.
