Exercise 4: prime generator
===========================

Question
--------

.. code-block:: text

   4. Write a generator that uses the sieve of Eratosthenes to generate prime numbers.

Solution
--------

``generate_primes`` implements an incremental dictionary-based sieve of
Eratosthenes. A composite candidate maps to the prime factors whose next
multiple it represents. A missing candidate is prime; it is yielded and its
square enters the dictionary. Composite entries move forward by their prime
steps.

The iterator yields primes forever in ascending order, so consumers must bound
iteration for finite results. Each call owns an independent sieve dictionary.
The dictionary grows as iteration advances; no machine-speed or memory-size
assumption is part of the public behavior.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run
---

Run the bounded, guarded demonstration:

.. code-block:: console

   $ uv run --python 3.10 python -m CH_07_generators_and_coroutines.exercise_04.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run --python 3.10 pytest CH_07_generators_and_coroutines/exercise_04/test_solution_00.py

Historical source
-----------------

The repository's initial answer is preserved in the immutable upstream
`original prime solution
<https://github.com/mastering-python/exercises/blob/500a31afac82e80f4ccd0b99da6fcd96bd9d8b3c/CH_07_generators_and_coroutines/exercise_04/solution_00.py>`_.
The local ``solution_01.py`` historical alternative remains byte-for-byte
unchanged.
