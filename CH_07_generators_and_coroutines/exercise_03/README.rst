Exercise 3: Fibonacci generator
===============================

Question
--------

.. code-block:: text

   3. Write a generator for the Fibonacci numbers.

Solution
--------

``fibonacci`` returns a new infinite iterator yielding
``0, 1, 1, 2, 3, ...``. Each iterator stores only its current pair of
arbitrary-precision Python integers. Separate calls have independent state,
and consumers must bound iteration when they need a finite result.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run
---

Run the bounded, guarded demonstration:

.. code-block:: console

   $ uv run --python 3.10 python -m CH_07_generators_and_coroutines.exercise_03.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run --python 3.10 pytest CH_07_generators_and_coroutines/exercise_03/test_solution_00.py

Historical source
-----------------

The repository's initial answer is preserved in the immutable upstream
`original Fibonacci solution
<https://github.com/mastering-python/exercises/blob/500a31afac82e80f4ccd0b99da6fcd96bd9d8b3c/CH_07_generators_and_coroutines/exercise_03/solution_00.py>`_.
The canonical solution and tests are self-contained.
