Exercise 2 - colored completion candidates
==========================================

The exercise asks:

::

   2. Add colors to the completer (hint: use `colorama` for the coloring).

Solution
--------

``ColorCompleter`` reuses the safe parser and completion behavior from
Exercise 1. Its ``complete`` method returns each inherited candidate unchanged,
including the ``None`` sentinel, so readline inserts plain valid Python rather
than ANSI escape bytes. On GNU readline, a registered completion-display hook
applies the configured Colorama foreground color only while listing choices,
then explicitly writes and flushes the fixed ``>>>`` prompt together with
readline's current input buffer. Calling ``redisplay()`` alone is insufficient
because a custom display hook does not receive the prompt. The default color is
``Fore.CYAN``; callers can pass another Colorama color with the keyword-only
``color`` argument. Every colored candidate ends with ``Style.RESET_ALL`` so
its color does not leak into later terminal output.

The guarded demonstration removes expression punctuation from readline's
completion delimiters so the callback receives complete attribute, bracket,
quoted-string, signed-number, complex-number, and tuple expressions. It
always registers the plain replacement callback. GNU readline additionally
receives the prompt-aware colored display hook and uses ``tab: complete``.
Python 3.10's macOS libedit backend ignores the display-hook API, so the
configuration safely degrades to libedit's plain candidate display and uses
``bind ^I rl_complete``. It never adds ANSI bytes to replacement text to force
color on libedit.

Exercise 2 adds no terminal, Colorama, or direct readline configuration during
import. Its terminal compatibility and direct readline setup happen only in the
guarded demonstration. On Python 3.10, a fresh import still reaches the
standard-library ``rlcompleter`` dependency through Exercise 1; that module
performs its own one-time readline registration. This inherited Exercise 1
integration behavior is outside the colored wrapper.

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

Run the optional real GNU readline PTY probe:

.. code-block:: console

   $ uv run --python 3.10 --group interactive --with gnureadline --with pexpect pytest CH_02_interactive_python/exercise_02/test_solution_00.py::test_gnu_readline_pty_restores_prompt_and_plain_buffer

Reference
---------

The chapter's original implementation is
`T_02_modifying_autocompletion.py <https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_02_interactive_python/T_02_modifying_autocompletion.py>`_.
