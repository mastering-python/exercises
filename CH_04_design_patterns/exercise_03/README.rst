Borg state per subclass
=======================

Question
--------

Create a Borg pattern that has a state per subclass.

Answer
------

``Borg`` keeps ordinary object identity while making instances of the same
exact class share one instance ``__dict__``.  It therefore differs from a
singleton: constructing a ``Borg`` repeatedly returns distinct objects, but
assignments and deletions stored in one instance's ``__dict__`` are visible
through every other instance of that exact class.  Attributes backed by
nonempty ``__slots__`` or other data descriptors can use per-instance storage
outside that dictionary and are not part of the shared-state contract.

The base class owns its own shared state.  Each subclass receives a fresh
state dictionary when the subclass is created, including subclasses of
subclasses.  State is consequently shared by instances of one exact class but
not inherited at runtime by sibling, parent, or grandchild instances.
Subclass ``__init__`` methods still run for every construction, so their
assignments update that exact class's shared state; merely constructing another
instance does not otherwise reset it.  Allocation is cooperative in multiple
inheritance: later ``__new__`` hooks in the method resolution order are called
with the constructor arguments and can consume or forward them.  A terminal
``object.__new__`` receives only the class, leaving ordinary constructor
arguments for the subclass initializer.

The Borg pattern is described in the immutable upstream reference:
https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_04_design_patterns/T_11_borg_and_singleton.rst

Dependencies
------------

The answer requires Python 3.10 or newer and uses only the standard library.
The focused test requires pytest from the repository's ``dev`` dependency
group.

Run
---

From the repository root:

.. code-block:: console

   $ uv run python CH_04_design_patterns/exercise_03/solution_00.py
   $ uv run pytest CH_04_design_patterns/exercise_03/test_solution_00.py
