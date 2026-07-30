Exercise 2: required base classes
=================================

Question
--------

.. code-block:: text

   2. Create a metaclass to test if specific classes are inherited.

Solution
--------

``ExpectedBasesMeta`` consumes the ``expected_bases`` class keyword in both
metaclass ``__new__`` and ``__init__``. Unrelated class keywords continue
cooperatively through both stages. The original namespace returned by
``__prepare__`` is forwarded by identity rather than copied, preserving custom
mapping behavior in a combined metaclass.

Before class construction, ``expected_bases`` must be a tuple containing only
types. Invalid values raise
``TypeError("<ClassName> expected_bases must be a tuple containing only types")``
before descriptor ``__set_name__`` or base ``__init_subclass__`` hooks can run.
Accepted tuple subclasses are iterated once into a built-in tuple; item
validation and completed-class checks reuse that snapshot. An empty requirement
tuple allows an ordinary class.

After that boundary check, the metaclass creates the class and uses
``issubclass`` against the completed class. Direct, indirect, multilevel, and
mixin inheritance therefore satisfy a requirement.

Every missing base is reported together in requested order. For example, a
class named ``Broken`` missing ``FirstBase`` and ``SecondBase`` raises
``TypeError("Broken must inherit FirstBase, SecondBase")``.

For a valid-shaped requirement tuple, missing-base validation after class
construction has an intentional tradeoff: descriptor ``__set_name__`` runs
first, then base ``__init_subclass__``, before the missing-base error is raised.
Their side effects are not rolled back. This timing is necessary to validate
the completed class and its full method resolution order.

``Trade`` is a valid example requiring ``SomeBaseClass``. The guarded module
demonstration prints whether that inheritance requirement is satisfied.

Dependencies
------------

The solution requires Python 3.10 or newer and has no third-party runtime
dependencies. Tests use the repository's pytest development dependency.

Run
---

Run the guarded demonstration from the repository root:

.. code-block:: console

   $ uv run python -m CH_08_metaclasses.exercise_02.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run pytest -W error CH_08_metaclasses/exercise_02/test_solution_00.py -v

Reference
---------

The completed-class check follows the ``issubclass`` behavior demonstrated in
`T_05_custom_type_checks.rst <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_08_metaclasses/T_05_custom_type_checks.rst>`_.
The solution is self-contained and does not import upstream material at
runtime.
