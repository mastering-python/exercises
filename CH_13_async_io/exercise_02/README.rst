Exercise 2: executor-backed synchronous operations
==================================================

Question
--------

The exact exercise-list question is:

.. code-block:: text

   Create an `asyncio` wrapper class for a synchronous process such as file or network operations using executors

Answer
------

``AsyncExecutor.run`` preserves each callable's parameter and result types and
submits a partial call through the current running loop's
``run_in_executor`` method. Results and worker exceptions propagate through
the await. New work is rejected after the adapter closes.

Without an injected executor, the adapter creates and owns a
``ThreadPoolExecutor``. ``close`` marks the adapter closed immediately, then
waits for owned-pool shutdown in a separate thread so the event loop remains
responsive and cancels queued futures. Repeated closes are harmless, and a
closed adapter rejects both new work and context re-entry. An injected
``concurrent.futures.Executor`` remains caller-owned; closing the adapter does
not shut it down. The same contract supports caller-managed thread and process
pools. Process-pool callables must be top-level and pickleable.

``AsyncioFile`` composes an ``AsyncExecutor`` and provides asynchronous
``pathlib.Path`` operations for ``exists``, text and byte reads and writes,
and ``rename``. It accepts an optional caller-owned ``AsyncExecutor`` runner
and closes only a runner it created itself. Text encoding and error handling
are keyword-only and default to ``"utf-8"`` and ``"strict"``. ``rename``
returns the new ``Path`` while the wrapper remains bound to the original path,
matching the underlying ``pathlib`` call.

Blocking socket operations use the same generic ``AsyncExecutor.run`` path as
files and process work. The tests use a local ``socketpair`` and require no
fixed port or external network service.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard
library. The repository's ``dev`` dependency group supplies pytest and the
static-analysis tools used by the tests.

Run
---

Run the guarded demonstration from the repository root:

.. code-block:: console

   $ uv run --python 3.10 python -m CH_13_async_io.exercise_02.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run --python 3.10 pytest CH_13_async_io/exercise_02/test_solution_00.py -v

Upstream references
-------------------

Executor usage is informed by
`T_05_executors.rst
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_13_async_io/T_05_executors.rst>`_
and the blocking-call warning by
`T_14_slow_blocking_code.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_13_async_io/T_14_slow_blocking_code.py>`_.
The upstream material is MIT licensed; no runtime clone or import is used.
