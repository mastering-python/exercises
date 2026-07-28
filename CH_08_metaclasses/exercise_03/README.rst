Exercise 3: wrapping methods
============================

Question
--------

.. code-block:: text

   3. Build a metaclass that wraps every method with a decorator (could be
   useful for logging/de- bugging purposes), something with a signature like
   this:

       class SomeClass(metaclass=WrappingMeta, wrapper=some_wrapper):

Solution
--------

``WrappingMeta`` accepts the optional ``wrapper`` class keyword. It wraps only
ordinary functions, static methods, and class methods defined directly in the
new class namespace. Static and class methods are rebuilt with their original
descriptor types, so their binding behavior remains intact.

Inherited methods, data attributes, properties and other descriptors, and
dunder methods remain untouched. Omitting ``wrapper`` or passing ``None``
leaves the namespace methods unchanged. ``WrappingMeta`` consumes ``wrapper``
cooperatively in both metaclass construction stages and forwards unrelated
class keywords.

``print_call`` is a generic example decorator. It preserves the wrapped
callable's metadata and signature, prints ``calling <name>``, and returns the
callable's result. ``SomeClass`` provides the guarded module demonstration.

Dependencies
------------

The solution requires Python 3.10 or newer and has no third-party runtime
dependencies. Tests use the repository's pytest development dependency.

Run
---

Run the example:

.. code-block:: console

   $ uv run python -m CH_08_metaclasses.exercise_03.solution_00

Run the tests:

.. code-block:: console

   $ uv run pytest CH_08_metaclasses/exercise_03/test_solution_00.py -v

Further reading
---------------

The metaclass class-keyword flow follows
`T_02_arguments_to_metaclasses.rst
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_08_metaclasses/T_02_arguments_to_metaclasses.rst>`_.
The distinction between class attributes and metaclass attributes is
illustrated in
`T_03_accessing_metaclass_attributes.rst
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_08_metaclasses/T_03_accessing_metaclass_attributes.rst>`_.

The solution and tests are self-contained; no source files are copied from
those references.
