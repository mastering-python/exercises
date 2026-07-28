Exercise 1 - safe finite-sequence completion
============================================

1. The `rlcompleter` enhancement we created currently only handles dictionaries. Try and extend the code so it supports lists, strings, and tuples as well.

Solution
--------

``Completer`` extends the standard-library ``rlcompleter.Completer`` with safe
name and item completion. Exact built-in dictionaries produce recursively safe
literal keys using ``repr``; non-finite numeric keys, keys nested beyond 64
tuple levels, and keys that exceed interpreter rendering limits are rejected.
Exact lists, tuples, and strings produce finite integer indices. Prefixes
filter candidates, and each request inspects at most 25 items. An explicitly
supplied namespace is shallow-copied once, and both completion paths use that
snapshot. Name completion includes Python hard keywords and built-ins without
inspecting namespace values.

Expressions are parsed with ``ast``. Only names, exact ``SimpleNamespace``
attributes containing safe containers, and exact built-in container subscripts
whose keys are safe literals are resolved. Calls and all other expression
forms are rejected, so completion never evaluates arbitrary Python code.
Importing the module does not register a ``readline`` completer or mutate
terminal state.

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
