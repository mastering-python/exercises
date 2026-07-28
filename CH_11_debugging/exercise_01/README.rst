Exercise 1: stalled-call diagnostics
====================================

Question
--------

.. code-block:: text

   1. Execute code with a timeout so you can see where your application is stalling

Solution
--------

``run_with_timeout_diagnostics`` schedules a one-time stack dump with
``faulthandler.dump_traceback_later`` before calling the supplied synchronous
callable. The diagnostic is cancelled in a ``finally`` block after either a
return or an exception. Positional and keyword arguments, return values, and
callable exceptions pass through unchanged.

The timeout must be greater than zero. Reaching it writes all thread stacks to
standard error, which can reveal the line where the application is stalled.
This is diagnostic only: it neither interrupts nor kills the callable. The
call therefore remains blocked until the callable itself returns or raises.
``faulthandler`` owns one process-wide delayed dump, so independently
scheduled diagnostics can replace one another.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run
---

Run the guarded demonstration:

.. code-block:: console

   $ uv run python -m CH_11_debugging.exercise_01.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest CH_11_debugging/exercise_01/test_solution_00.py -v

Historical source
-----------------

The diagnostic approach is illustrated by the immutable upstream
`T_06_stack.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_11_debugging/T_06_stack.py>`_
and
`T_07_faulthandler.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_11_debugging/T_07_faulthandler.py>`_.
The solution and tests are self-contained; no source files are copied from
those references.
