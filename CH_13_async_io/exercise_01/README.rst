Exercise 1: registered async resources
======================================

Question
--------

The exact exercise-list question is:

.. code-block:: text

   Try to create a `asyncio` base class that automatically registers all instances for easy closing/destructuring when you are done

Answer
------

``AsyncBase`` registers each concrete instance when its constructor calls
``super().__init__()``. Subclasses implement only the abstract asynchronous
``_close`` hook. ``close`` is idempotent after successful cleanup. A failed
cleanup leaves the instance registered and eligible for another attempt.
Neither ``AsyncBase`` nor ``AsyncManager`` starts an event loop or performs
asynchronous work from a destructor.

``AsyncBase.pending_count()`` reports the shared registry size.
``AsyncBase.close_all()`` takes a stable snapshot and attempts its resources
in last-in, first-out order. Successful resources are unregistered. Ordinary
``Exception`` instances are collected in attempt order and raised together as
the ``RuntimeError`` subclass ``CloseFailures``. Its ``failures`` attribute is
the immutable exception tuple. ``BaseException`` subclasses, including
``asyncio.CancelledError``, propagate immediately instead of being converted
to cleanup failures.

``AsyncManager`` is a no-argument asynchronous context manager over that
registry. It always attempts cleanup when the body exits. With a successful
body, cleanup failures propagate normally. When both the body and cleanup
fail, ``close_all`` propagation is unchanged: ``CloseFailures`` is raised and
the body exception remains available through normal exception context. A
cleanup ``BaseException`` remains control flow and propagates immediately.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard
library. The repository's ``dev`` dependency group supplies pytest and the
static-analysis tools used by the tests.

Run
---

Run the guarded demonstration from the repository root:

.. code-block:: console

   $ uv run --python 3.10 python -m CH_13_async_io.exercise_01.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run --python 3.10 pytest CH_13_async_io/exercise_01/test_solution_00.py -v

Upstream references
-------------------

The explicit async constructor and destructor pattern is informed by
`T_12_constructors_and_destructors.rst
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_13_async_io/T_12_constructors_and_destructors.rst>`_
and task shutdown by
`T_18_wait_for_all_tasks.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_13_async_io/T_18_wait_for_all_tasks.py>`_.
The upstream material is MIT licensed; this solution is self-contained.
