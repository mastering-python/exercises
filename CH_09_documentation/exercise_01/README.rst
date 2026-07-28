Exercise 1: type hint a complex dict
====================================

Question
--------

1. Type hint a complex `dict`

Solution
--------

``TypedDict`` fits a dictionary with fixed keys whose values have different
types.  ``UserRecord`` records the type associated with each required key,
while the nested ``Contact`` type gives the contact dictionary its own reusable
shape.  The phone field accepts either a string or ``None``.

These declarations support static type checkers.  They do not validate values,
convert input, or create a new runtime record type: values remain ordinary
``dict`` objects at runtime.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run the guarded module demonstration:

.. code-block:: console

   $ uv run python -m CH_09_documentation.exercise_01.solution_00
   Ada (36) active: ada@example.test

Run the focused tests:

.. code-block:: console

   $ uv run pytest -W error CH_09_documentation/exercise_01/test_solution_00.py

Historical source
-----------------

The chapter's type-hinting discussion is preserved in
`T_00_type_hinting.rst <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_09_documentation/T_00_type_hinting.rst>`_.
