Exercise 5 - search IPython history
===================================

The exercise asks:

::

   5. Try and create a script that will look for a given pattern through all of your previous ipython sessions.

Solution
--------

``search_history`` compiles one Python regular expression, applies ``re.search``
to each complete raw input, and returns immutable ``HistoryMatch`` values sorted
by session and line. The input may span multiple lines. Use inline flags such as
``(?m)`` when ``^`` and ``$`` should match individual lines, or ``(?s)`` when
``.`` should match newlines. An invalid expression raises ``re.error``.

``iter_ipython_history`` uses IPython's ``HistoryAccessor`` to request raw,
non-unique input from every stored session. An injected accessor remains owned
by its caller. An accessor created by the iterator is closed after exhaustion,
an error, or early generator closure.

The command prints each match as ``session:line: source`` and exits with status
zero when at least one match exists or status one when none exists.

Privacy warning
---------------

By default, the command reads the local IPython history database for the current
profile. That history can contain code, paths, URLs, tokens, and other sensitive
input. Review the regular expression and output destination before running it.
Importing the module does not construct a history accessor or read a profile.
The tests use a temporary SQLite history database and never read user history.

Requirements
------------

Python 3.10+ and IPython are required. Run the command with the interactive
dependency group:

.. code-block:: console

   $ uv run --group interactive python -m CH_02_interactive_python.exercise_05.solution_00 'pattern'

Run the focused tests with:

.. code-block:: console

   $ uv run --group interactive pytest CH_02_interactive_python/exercise_05/test_solution_00.py -W error

Reference
---------

The original approach is preserved in the immutable
`upstream session_filename.ipy <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_02_interactive_python/session_filename.ipy>`_.
