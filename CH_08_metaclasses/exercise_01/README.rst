Exercise 1: required class attributes
=====================================

Question
--------

1. Create a metaclass to test if attributes/methods are available.

Solution
--------

``ExpectedAttrsMeta`` first creates the class and then validates the requested
attribute names with ``hasattr``.  Checking the completed class means attributes
defined by direct, indirect, or multiple inheritance satisfy the contract.
Every missing name is reported together in the order requested.

``Trade`` is a valid example requiring ``buy`` and ``sell``.  Its methods return
``"buy"`` and ``"sell"`` respectively.

Dependencies
------------

The solution requires Python 3.10 or newer and has no third-party runtime
dependencies.  Tests use the repository's pytest development dependency.

Run
---

Run the guarded demonstration from the repository root:

.. code-block:: console

   $ uv run python -m CH_08_metaclasses.exercise_01.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest CH_08_metaclasses/exercise_01/test_solution_00.py -v

Reference
---------

The class-construction pattern is informed by
`T_01_basic_metaclass.rst <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_08_metaclasses/T_01_basic_metaclass.rst>`_.
The solution is self-contained and does not import the upstream material at
runtime.
