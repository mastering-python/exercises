Exercise 3: live-instance manager
=================================

Question
--------

.. code-block:: text

   3. Try to create a memory manager for your classes that warns you when more than a configured number of instances remain in memory. If you never expect more than 5 instances of a certain class, you can warn the user when that number is exceeded.

Solution
--------

``InstanceManager`` creates instances of one configured class and tracks those
instances with weak references. ``live_count`` reports how many remain alive,
and ``instances`` returns the live objects in deterministic creation order.
Collection removes an object from both views without the manager extending its
lifetime. Separate managers, including managers for a base class and a
subclass, keep isolated state.

Only objects made through ``create`` are tracked. The limit must be positive.
Creating an object above it emits ``ResourceWarning``. An object type that
does not support weak references is rejected after construction without
leaving a tracked entry. The callback holds only a weak reference to its
manager, so keeping a created object alive does not keep the manager alive.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run
---

Run the guarded demonstration:

.. code-block:: console

   $ uv run python -m CH_12_performance.exercise_03.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest CH_12_performance/exercise_03/test_solution_00.py -v

Historical source
-----------------

The immutable upstream references are
`T_13_memory_leaks.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_12_performance/T_13_memory_leaks.py>`_,
`T_15_garbage_collector_viewing.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_12_performance/T_15_garbage_collector_viewing.py>`_,
and
`T_16_weak_references.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_12_performance/T_16_weak_references.py>`_.
The solution and tests are self-contained; no source files are copied from
those references.
