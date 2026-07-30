Exercise 1: spawn-safe process echo
===================================

Question
--------

The original exercise question is:

.. code-block:: text

   1. See if you can make an echo server and client as separate processes. Even though we did not cover `multiprocessing.Pipe()`, I trust you can work with it regardless. It can be created through `a, b = multiprocessing.Pipe()` and you can use it with `a.send()` or `b.send()` and `a.recv()` or `b.recv()`.

Solution
--------

``EchoRequest``, ``EchoReply``, and ``StopRequest`` are frozen dataclasses that
define the duplex pipe protocol. ``echo_server(connection)`` is a top-level,
spawn-safe child target. It validates request identifiers and message types,
returns identified replies in order, preserves empty strings, and exits through
a cooperative ``StopRequest``.

``run_echo_session(messages, timeout=5.0, context=None)`` validates a finite,
positive timeout and every string before spawning. It uses a spawn context by
default, applies one deadline to reply polling and child joining, validates
reply type, identifier, message, and child exit code, and always closes both
local endpoints. Normal completion uses the cooperative stop and bounded join.
Failure cleanup terminates and joins a still-running child.

Dependencies
------------

The solution uses only the Python 3.10 standard library. Tests use the
repository's ``pytest`` development dependency.

Run the guarded demonstration:

.. code-block:: console

   uv run python -m CH_14_multithreading_and_multiprocessing.exercise_01.solution_00

Run the focused tests:

.. code-block:: console

   uv run pytest CH_14_multithreading_and_multiprocessing/exercise_01/test_solution_00.py -vv

Reference
---------

The implementation builds on the chapter's immutable
`multiprocessing process example
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_03_multiprocessing.py>`_
and
`multiprocessing class example
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_14_multithreading_and_multiprocessing/T_04_multiprocessing_class.py>`_.
The upstream material is MIT licensed; this solution is self-contained.
