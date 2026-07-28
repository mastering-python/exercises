Exercise 1 - safe finite-sequence completion
============================================

1. `rlcompleter` enhancement we created currently only handles dictionaries. Try extend code so supports lists, strings, tuples well.

Solution
--------

``Completer`` extends the standard-library ``rlcompleter.Completer`` with item
completion. Mappings produce their keys using ``repr``; lists, tuples, and
strings produce their finite integer indices. Prefixes filter candidates and
each request inspects at most 25 items.

Expressions are parsed with ``ast``. Only names, attributes, and subscripts
whose keys are literals are resolved. Calls and all other expression forms are
rejected, so completion never evaluates arbitrary Python code. Importing the
module does not register a ``readline`` completer or mutate terminal state.

Dependencies
------------

The solution uses only the Python standard library. The repository's ``dev``
dependency group supplies pytest and the static-analysis tools.

Run the demonstration:

.. code-block:: console

   uv run python CH_02_interactive_python/exercise_01/solution_00.py

Run the focused tests:

.. code-block:: console

   uv run pytest CH_02_interactive_python/exercise_01/test_solution_00.py

Reference
---------

The chapter's original dictionary-only implementation is
`T_02_modifying_autocompletion.py <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_02_interactive_python/T_02_modifying_autocompletion.py>`_.
