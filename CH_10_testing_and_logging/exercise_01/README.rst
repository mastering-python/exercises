Exercise 1: testing and logging utilities
=========================================

This exercise answers all five Chapter 10 questions.  The public entry point is
``CH_10_testing_and_logging.exercise_01.solution_00``; focused implementation
modules keep doctest discovery, pytest collection, and logging independent.

Question 1: run doctests for one object
---------------------------------------

``run_doctests(target, *, optionflags=doctest.ELLIPSIS)`` recursively discovers
examples attached to a function or class and returns one aggregate
``doctest.TestResults``.  A class includes examples on discoverable methods.
Targets without examples return zero failures and zero attempts.

The function uses a fresh finder and runner for every call.  A reentrant lock
serializes calls because ``doctest.DocTestRunner`` temporarily changes
process-wide state.  Code that invokes ``doctest`` directly does not share that
lock.  Exceptions such as ``KeyboardInterrupt`` propagate.  A locally defined
function or class with a valid ``__name__`` can refer to itself in its examples.

Question 2: run doctests for a module
-------------------------------------

``run_module_doctests(target, *, optionflags=doctest.ELLIPSIS)`` is the explicit
module-recursive API.  ``target`` must be a ``types.ModuleType``; any other
value raises ``TypeError``.  It aggregates the module docstring and examples on
module-owned, discoverable functions, classes, and methods.

Discovery follows ``doctest.DocTestFinder(recurse=True)``.  Objects hidden in a
closure, generated dynamically without a module attribute, or imported from
another module are not treated as recursively owned members.  ``optionflags=0``
enables exact comparison instead of the default ellipsis matching.

Question 3: require file-level test documentation
-------------------------------------------------

``file_documentation_plugin.py`` provides the pytest 9
``pytest_collect_file(file_path: pathlib.Path, parent)`` hook.  It checks only
``.py`` files whose basenames match the active ``python_files`` configuration.
A non-empty, syntactically real module docstring is accepted.  Missing
docstrings, malformed source, unreadable files, and invalid encodings become
clear collection errors.  Non-test Python files are left to other collectors.

Load the plugin explicitly:

.. code-block:: console

   $ uv run pytest -p CH_10_testing_and_logging.exercise_01.file_documentation_plugin

The plugin validates source during collection; it does not alter test execution
or require documentation on non-Python collectors.

Question 4: run static analysis with tox
----------------------------------------

``tox.ini`` defines the named tox 4 environment ``static``.  It selects Python
3.10, skips package construction, installs ``mypy`` and ``pytest`` (which the
plugin imports), changes to the repository root, and checks only the maintained
Chapter 10 implementation files.  It does not run pytest or recursively analyze
the rest of the repository.

Run it from the repository root:

.. code-block:: console

   $ uv run --group packaging tox -c CH_10_testing_and_logging/exercise_01/tox.ini -e static

Question 5: batch logging records by task ID
--------------------------------------------

``TaskBatchLoggerAdapter`` is a thread-safe ``logging.LoggerAdapter``.
``record(task_id, level, message, *args)`` appends one message to a task-local
batch.  ``flush(task_id)`` emits one record and removes the flushed messages.
Messages keep insertion order and use a newline separator.  Percent-style
logging arguments are formatted at flush time.  The record level is the highest
numeric level in the batch.

Adapter ``extra`` values are copied to the combined record, and the flushed
``task_id`` overrides any adapter-level ``task_id``.  Empty IDs raise
``ValueError``; non-string IDs raise ``TypeError``; flushing an unknown or empty
batch raises ``KeyError``.  ``pending_count(task_id)`` reports buffered work.
``discard(task_id)`` is the only operation that intentionally drops a batch and
returns the number of messages removed.

If the combined level is disabled, a logger filter rejects the record, or every
eligible handler rejects it by level or filter, ``flush`` returns ``False`` and
retains the batch.  Formatting failures and handler failures reported through
the standard ``handleError`` path propagate and also retain it for retry or
explicit discard.  With multiple handlers, retrying after a later handler fails
can duplicate the record in an earlier handler that already accepted it.  A
successful flush returns ``True``.  Standard adapter logging methods remain
immediate; batching uses ``record`` and ``flush``.  Batches are in-memory only
and are not durable across process termination.

Dependencies and commands
-------------------------

The doctest and logging solutions require Python 3.10 or newer and use the
standard library.  The collection plugin requires ``pytest>=9.0``.  The tox
environment requires ``tox>=4.30`` and installs its own ``mypy>=1.18`` and
``pytest>=9.0`` dependencies.  Repository development groups provide these
tools.

Run the demonstration:

.. code-block:: console

   $ uv run python -m CH_10_testing_and_logging.exercise_01.solution_00
   Attempted 1 doctest; 0 failed.

Run every focused exercise test:

.. code-block:: console

   $ uv run pytest -q CH_10_testing_and_logging/exercise_01

Run the three added suites independently:

.. code-block:: console

   $ uv run pytest -q CH_10_testing_and_logging/exercise_01/tests_doctests/test_solution_00.py
   $ uv run pytest -q CH_10_testing_and_logging/exercise_01/tests_plugin/test_solution_00.py
   $ uv run pytest -q CH_10_testing_and_logging/exercise_01/tests_task_logging/test_solution_00.py

Historical source
-----------------

The book repository's original exercise source is available at
`T_00_simple_doctest.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_10_testing_and_logging/T_00_simple_doctest.py>`_.
