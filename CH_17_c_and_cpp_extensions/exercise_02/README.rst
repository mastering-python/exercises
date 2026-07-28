Exercise 2: checked native custom sum
=====================================

Question
--------

.. code-block:: text

   2. Try to make the `custom_sum` function we created safer by adding proper errors for overflow/underflow issues. Additionally, catch the errors when summing multiple numbers that only overflow or underflow in summation.

Answer
------

``custom_sum`` accepts an integer sequence, rejects booleans and non-integers
before native execution, and leaves the input unchanged. The extension checks
every ``PyLong_AsLongLong`` conversion immediately, preserving Python's
``TypeError`` and ``OverflowError`` instead of replacing them.

Before each addition, the C loop checks the signed ``long long`` bounds.
Cumulative overflow and underflow raise distinct ``OverflowError`` messages.
Opposite-signed values may safely cancel, and an empty sequence returns zero.

Native compilation uses the repository's ``native`` dependency group. Both
the tests and guarded demonstration compile into temporary directories through
the shared builder, so no extension or object files are left in the repository.

Run
---

Run the guarded demonstration:

.. code-block:: console

   $ uv run --group native python -m CH_17_c_and_cpp_extensions.exercise_02.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run --group native pytest CH_17_c_and_cpp_extensions/exercise_02/test_solution_00.py -vv

Upstream reference
------------------

The immutable upstream reference is
`T_12_silent_or_lethal_errors.c
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_17_c_and_cpp_extensions/T_12_silent_or_lethal_errors.c>`_.
The upstream repository is MIT licensed. This solution is self-contained and
does not copy or import that source file at runtime.
