Exercise 2: required base classes
=================================

Question
--------

.. code-block:: text

   2. Create a metaclass to test if specific classes are inherited.

Solution
--------

``ExpectedBasesMeta`` consumes the ``expected_bases`` class keyword and
forwards unrelated class keywords through normal class construction. It copies
the supplied namespace, creates the class, then uses ``issubclass`` against the
completed class. Direct, indirect, multilevel, and mixin inheritance therefore
satisfy a requirement. An empty requirement tuple allows an ordinary class.

Every missing base is reported together in requested order. For example, a
class named ``Broken`` missing ``FirstBase`` and ``SecondBase`` raises
``TypeError("Broken must inherit FirstBase, SecondBase")``.

Validation after class construction has an intentional tradeoff:
``__init_subclass__`` and descriptor ``__set_name__`` hooks have already run
before a missing-base error is raised. Their side effects are not rolled back.
This timing is necessary to validate the completed class and its full method
resolution order.

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
