Exercise 7: constrained runtime type checking
=============================================

Question
--------

The relevant chapter exercise-list excerpt is:

.. code-block:: text

   1. Extend `track` function monitor execution time.
   2. Extend `track` function min/max/average execution time call count.
   3. Modify memoization function function unhashable types.
   4. Modify memoization function cache per function instead global one.
   5. Create version `functools.cached_property` can be recalculated as needed.
   6. Create single-dispatch decorator considers all configurable number arguments instead only first one.
   7. Enhance the `type_check` decorator to include additional checks such as requiring a number to be greater than or less than a given value.

Solution
--------

``Constraint`` defines the ``validate(name, value) -> None`` protocol.
The frozen ``GreaterThan``, ``LessThan``, and ``Between`` implementations
accept finite real-number bounds and never coerce values. Boolean values are
not treated as numbers. Non-finite float bounds are rejected at construction,
and non-finite float call values are rejected before comparison. Huge finite
integers and finite fractions remain supported. ``Between`` requires its lower
bound to be less than its upper bound. Its interval is exclusive by default;
``inclusive=True`` includes both boundary values.

``type_check(**constraints)`` binds each call against the decorated function's
signature and applies defaults. It first checks every annotated parameter,
including parameters without constraints, using runtime instance checks. It
then validates configured parameters. ``Literal`` matching requires both exact
runtime type and equality, so equal values such as ``1`` and ``True`` remain
distinct. Type hints resolve lazily on the first call, with defining locals and
the runtime class available for forward references. Only a successful complete
resolution is cached; unresolved names therefore raise when called rather than
when decorated.

Unknown parameter names, constraints targeting ``*args`` or ``**kwargs``, and
objects without a callable ``validate`` method are rejected when the function
is decorated. Unconstrained variadic annotations are supported and checked
element by element.

Parameter type mismatches, booleans, and other nonnumeric constrained values
raise ``TypeError``. Non-finite numeric values and numeric constraint
violations raise ``ValueError``. Normal signature-binding, annotation
resolution, and wrapped-function exceptions propagate unchanged. Return
annotations are intentionally not checked. ``functools.wraps`` keeps the
original metadata, wrapped function, and inspectable signature.

For naming compatibility, ``Gt`` is an alias of ``GreaterThan`` and
``enforce_type_hints`` is an alias of ``type_check``.

Dependencies
------------

The solution has no third-party runtime dependencies and requires Python 3.10
or newer. Tests use the repository's ``pytest`` development dependency.

Run the silent, guarded module demonstration:

.. code-block:: console

   uv run python -m CH_06_decorators.exercise_07.solution_00

Run focused tests with warnings treated as errors:

.. code-block:: console

   uv run pytest -W error CH_06_decorators/exercise_07 -v

Reference
---------

The solution extends the chapter's `validation discussion
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_06_decorators/T_15_validation.rst>`_.
