Exercise 6: configurable multi-argument single dispatch
========================================================

Question
--------

The relevant chapter exercise-list excerpt is:

.. code-block:: text

   1. Extend the `track` function to monitor execution time.
   2. Extend the `track` function with min/max/average execution time and call count.
   3. Modify the memoization function to function with unhashable types.
   4. Modify the memoization function to have a cache per function instead of a global one.
   5. Create a version of `functools.cached_property` that can be recalculated as needed.
   6. Create a single-dispatch decorator that considers all or a configurable number of arguments instead of only the first one.

Solution
--------

``fancysingledispatch`` creates a dispatcher for a base function. By default,
every base parameter contributes to the dispatch key. The legacy positional
form, such as ``@fancysingledispatch("context")``, and true-keyword form, such
as ``@fancysingledispatch(context=True)``, exclude named parameters. The
explicit ``dispatch_on=("left", "right")`` form selects parameters in the
given order and cannot be combined with either legacy form.

A call is bound against the base signature and defaults are applied before the
key is built. The key is the tuple of exact runtime types for selected
arguments. Registry lookup deliberately performs no subclass or method
resolution order fallback. An unregistered tuple calls the base function.

``dispatcher.register(function)`` is a decorator and returns ``function``.
Registered functions must have exactly the base parameter names and kinds.
Every selected parameter needs an annotation that ``typing.get_type_hints``
resolves to a concrete class. Missing annotations, ``typing.Any``, unions,
parameterized generics, and other non-class annotations are rejected.
Registering an existing type tuple replaces its implementation.

Configuration rejects false compatibility keywords, conflicting selection
styles, empty or duplicate selections, duplicate exclusions, and unknown
parameter names. Normal signature-binding errors propagate unchanged.
``functools.wraps`` preserves base metadata, ``__wrapped__``, and the
inspectable signature.

Running
-------

Run the silent, guarded module demonstration:

.. code-block:: console

   uv run python -m CH_06_decorators.exercise_06.solution_00

Run focused tests with warnings treated as errors:

.. code-block:: console

   uv run pytest -W error CH_06_decorators/exercise_06 -v

Reference
---------

The solution extends the chapter's
`single-dispatch discussion <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_13_single_dispatch.rst>`_.
