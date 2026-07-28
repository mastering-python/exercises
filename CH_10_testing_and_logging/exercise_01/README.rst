Exercise 1: run doctests
========================

Question
--------

1. Create a function that tests the doctests of a given function/class.

Solution
--------

``run_doctests`` uses one recursive ``doctest.DocTestFinder`` to discover
examples attached to the target and its members. One ``doctest.DocTestRunner``
runs every discovered test, so the returned ``doctest.TestResults`` contains
the aggregate ``failed`` and ``attempted`` totals. A target without examples
returns zero for both totals.

Doctest failures are written to the runner's normal report and counted in the
result rather than raised as exceptions. ``doctest.ELLIPSIS`` matching is
enabled by default. Pass a different ``optionflags`` value, including ``0`` for
exact matching, to control doctest comparison.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run the guarded module demonstration:

.. code-block:: console

   $ uv run python -m CH_10_testing_and_logging.exercise_01.solution_00
   Attempted 1 doctest; 0 failed.

Run the focused tests:

.. code-block:: console

   $ uv run pytest -W error CH_10_testing_and_logging/exercise_01/test_solution_00.py

Historical source
-----------------

The chapter's basic doctest example is preserved in
`T_00_simple_doctest.py <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_10_testing_and_logging/T_00_simple_doctest.py>`_.
