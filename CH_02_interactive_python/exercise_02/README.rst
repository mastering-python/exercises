Exercise 2 - colored completion candidates
==========================================

The exercise asks:

::

   2. Add colors to the completer (hint: use `colorama` for the coloring).

Solution
--------

``ColorCompleter`` reuses the safe parser and completion behavior from
Exercise 1, then wraps every non-``None`` candidate in the configured Colorama
foreground color. The default is ``Fore.CYAN``; callers can pass another
Colorama color with the keyword-only ``color`` argument. Every candidate ends
with ``Style.RESET_ALL`` so its color does not leak into later terminal output.
The ``None`` sentinel remains unchanged.

Exercise 2 adds no terminal, Colorama, or readline configuration during import.
Its terminal compatibility and direct readline setup happen only in the guarded
demonstration. On Python 3.10, a fresh import still reaches the standard-library
``rlcompleter`` dependency through Exercise 1; that module performs its own
one-time readline registration. This inherited Exercise 1 integration behavior
is outside the colored wrapper.

Dependencies
------------

The solution requires Python 3.10+ and Colorama. The repository's
``interactive`` dependency group supplies Colorama, while its default ``dev``
group supplies pytest and the static-analysis tools.

Run the module:

.. code-block:: console

   $ uv run --group interactive python -m CH_02_interactive_python.exercise_02.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run --group interactive pytest CH_02_interactive_python/exercise_02/test_solution_00.py

Reference
---------

The chapter's original implementation is
`T_02_modifying_autocompletion.py <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_02_interactive_python/T_02_modifying_autocompletion.py>`_.
