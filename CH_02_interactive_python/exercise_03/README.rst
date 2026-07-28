Exercise 3 - Jedi static source completion
==========================================

The exercise asks:

::

   3. Instead of manually completing using our own object introspection, try and use the `jedi` library for autocompletion, which does static code analysis.

Solution
--------

``complete_source`` passes the source text to ``jedi.Script`` and returns the
sorted, deduplicated ``name_with_symbols`` completion spellings. Jedi performs
static analysis: the supplied source is never executed, even when it contains
function calls or other runtime side effects. Importing the solution is also
side-effect free; only the guarded module demonstration prints output.

``line`` uses Jedi's one-based line numbering and ``column`` is a zero-based
offset within that line. When omitted, both coordinates target the end of the
source as represented by ``source.splitlines() or [""]``. Explicit lines must
be between 1 and the number of represented lines, and columns must be between
0 and the selected line's length. Invalid coordinates raise ``ValueError``.

Incomplete or invalid Python is passed unchanged to Jedi for best-effort
completion. Jedi and dependency failures propagate to the caller.

Dependencies
------------

The solution requires Python 3.10+ and Jedi. The repository's ``interactive``
dependency group supplies Jedi, while the default ``dev`` group supplies
pytest and the static-analysis tools.

Run the guarded module demonstration:

.. code-block:: console

   $ uv run --group interactive python -m CH_02_interactive_python.exercise_03.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run --group interactive pytest CH_02_interactive_python/exercise_03/test_solution_00.py

Reference
---------

The question comes from the immutable `upstream Chapter 2 exercise list
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_02_interactive_python/README.rst>`_.
