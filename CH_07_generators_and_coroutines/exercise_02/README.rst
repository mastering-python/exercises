Exercise 2: sliceable generator
===============================

Question
--------

.. code-block:: text

   2. Create a class that wraps a generator so it becomes sliceable by using `itertools.islice()` internally.

Solution
--------

``SliceableGenerator`` converts its input iterable to one iterator and stores
that iterator for the wrapper's lifetime. Every slice is interpreted relative
to the iterator's current position, so an access consumes skipped values as
well as returned values. Later accesses continue after everything consumed by
earlier accesses.

Omitted start, stop, and step values are supported, and a positive step is
passed through to ``itertools.islice``. Integer indexing is rejected because
the wrapper accepts slices only. Negative bounds and nonpositive steps are
also rejected. The wrapper cannot rewind, and an omitted stop will not
terminate when the underlying iterator is infinite.

Dependencies
------------

The solution requires Python 3.10 or newer and uses only the standard library.
The repository's ``dev`` dependency group supplies pytest for the tests.

Run
---

Run the bounded, guarded demonstration:

.. code-block:: console

   $ uv run --python 3.10 python -m CH_07_generators_and_coroutines.exercise_02.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run --python 3.10 pytest CH_07_generators_and_coroutines/exercise_02/test_solution_00.py

Historical source
-----------------

The standard slicing discussion is preserved in the immutable upstream
`T_07_islice.rst source
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_07_generators_and_coroutines/T_07_islice.rst>`_.
The canonical solution and tests are self-contained.
