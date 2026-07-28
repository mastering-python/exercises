Exercise 4 - editable Hello widget
==================================

The exercise asks:

::

    4. Try to create a `Hello` `<ipywidget>` so the name of the person can be edited through a notebook without code changes.

Solution
--------

``create_hello_widget`` returns an immutable bundle containing a text input, a
greeting label, and a vertical container. Editing the text input updates the
existing label immediately. Leading and trailing whitespace is removed from the
greeting; an empty or whitespace-only name displays ``Hello, World!``.

Each call creates independent widget state. Importing the module and creating
the bundle are headless: neither operation displays a widget, opens a browser,
nor requires a running notebook. ``main`` imports IPython's display helper only
when called and displays the container.

Call ``hello.close()`` when the bundle is no longer needed. Cleanup is
idempotent, unregisters only the bundle's own observer, and closes the input,
label, and container. Observers registered by callers remain untouched.

Notebook usage:

.. code-block:: python

    from IPython.display import display

    from CH_02_interactive_python.exercise_04.solution_00 import (
        create_hello_widget,
    )

    hello = create_hello_widget("Ada")
    display(hello.container)

Dependencies
------------

The solution requires Python 3.10+, ipywidgets, and IPython. The repository's
``interactive`` dependency group supplies both packages; the default ``dev``
group supplies pytest and the static-analysis tools.

Run the guarded module demonstration:

.. code-block:: console

    $ uv run --group interactive python -m CH_02_interactive_python.exercise_04.solution_00

Run the focused tests without opening a notebook or browser:

.. code-block:: console

    $ uv run --group interactive pytest CH_02_interactive_python/exercise_04/test_solution_00.py

Reference
---------

The question is preserved from the immutable
`upstream Chapter 2 exercise list
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_02_interactive_python/README.rst>`_.
