Exercise 2: interactive Datashader notebook
============================================

Question
--------

.. code-block:: text

   Make the datashater plot interactive using a Jupyter notebook.

Solution
--------

``build_interactive_plot`` reuses exercise 1's deterministic renderer behind
an ``ipywidgets.IntSlider``. Resolution is bounded from 32 through 256 pixels,
in steps of 32, with a default of 64. A value-change callback refreshes an
``ipywidgets.Output`` without duplicating output. Call
``dispose_interactive_plot`` when finished to unregister the callback, close
the slider, output, and container, and release the captured DataFrame.

``datashader_interactive.ipynb`` loads only the committed six-row fixture,
builds the widget, and asserts the fixture shape and default resolution. It
discovers the repository root from the current directory and its parents,
adding that root to ``sys.path`` only when needed. It is a clean nbformat 4
notebook with a Python 3 kernelspec, deterministic cell IDs, no execution
counts, no outputs, and no saved widget state. Tests execute in-memory copies
from both the repository root and notebook directory through nbclient with a
bounded timeout; no network access is required.

Dependencies
------------

Python 3.10 or newer is required. The repository's ``scientific`` dependency
group supplies pandas, Datashader, Pillow, ipywidgets, nbformat, nbclient,
ipykernel, jupyter-client, and JupyterLab. The ``dev`` dependency group
supplies pytest and pytest-timeout.

Run
---

Open the notebook from the repository root:

.. code-block:: console

   $ uv run --group scientific jupyter lab CH_15_scientific_python/exercise_02/datashader_interactive.ipynb

The notebook also executes when Jupyter starts in its own directory:

.. code-block:: console

   $ cd CH_15_scientific_python/exercise_02
   $ uv run --group scientific jupyter lab datashader_interactive.ipynb

Run the focused tests, including headless notebook execution:

.. code-block:: console

   $ uv run --group scientific pytest CH_15_scientific_python/exercise_02/test_solution_00.py -vv

Reference
---------

The implementation is informed by the chapter's immutable
`Datashader notebook
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_15_scientific_python/T_17_datashader.ipynb>`_.
The upstream material is MIT licensed; this exercise solution is
self-contained.
