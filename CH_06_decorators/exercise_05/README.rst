Exercise 5: recalculable cached property
========================================

Question
--------

The relevant chapter exercise-list excerpt is:

1. Extend the `track` function to monitor execution time.
2. Extend the `track` function with min/max/average execution time and call count.
3. Modify the memoization function to function with unhashable types.
4. Modify the memoization function to have a cache per function instead of a global one.
5. Create a version of `functools.cached_property` that can be recalculated as needed.

Solution
--------

``CachedProperty[T, R]`` is a generic descriptor that stores each computed
result under the descriptor's bound attribute name in that instance's
``__dict__``.  Instances therefore cache independently.  Class access returns
the descriptor itself.

The first instance access calls the decorated function and stores its result,
including ``None``, only after the function returns successfully.  Later
accesses reuse that value.  Deleting the property removes only that instance's
cached value, so the next access recalculates it.  Deletion before calculation
raises ``AttributeError`` naming the property.

The descriptor rejects access before ``__set_name__`` and rejects binding one
descriptor to two different names.  Instances without a ``__dict__`` are not
supported and raise a clear ``TypeError``.  Function metadata is retained.

This teaching implementation provides no locking or thread-safety guarantee.
Concurrent access may calculate the value more than once.

Running
-------

Run the solution module:

.. code-block:: console

   uv run python -m CH_06_decorators.exercise_05.solution_00

Run the exercise tests:

.. code-block:: console

   uv run pytest -W error CH_06_decorators/exercise_05 -v

Reference
---------

The solution extends the chapter's
`properties and descriptors discussion <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_10_properties.rst>`_.
