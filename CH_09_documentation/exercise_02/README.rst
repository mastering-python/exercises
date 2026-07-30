Exercise 2: type hint nested measurements
=========================================

Question
--------

1. Type hint a complex `dict`
2. Type hint nested types

Solution
--------

``NestedMeasurements`` gives the nested
``dict[str, list[tuple[int, float]]]`` shape a readable name.  The alias helps
static type checkers and documents the relationship between level names,
integer identifiers, and floating-point measurements.  It does not add runtime
validation or create a new container type.

``flatten_measurements`` visits mapping values in dictionary insertion order and
rows in list order, returning each tuple's floating-point measurement component.
It creates a new list and does not mutate the input containers.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run
---

Run the guarded demonstration from the repository root:

.. code-block:: console

   $ uv run python -m CH_09_documentation.exercise_02.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest -W error CH_09_documentation/exercise_02/test_solution_00.py

Historical source
-----------------

The chapter's type-hinting discussion is preserved in
`T_00_type_hinting.rst <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_09_documentation/T_00_type_hinting.rst>`_.
