Exercise 1: deterministic Datashader plot
=========================================

Question
--------

.. code-block:: text

   Create a datashader plot.

Solution
--------

``points.csv`` is an exact six-row local fixture with ``x``, ``y``, and
``category`` columns. ``load_points`` rejects any other column layout, empty
input, and nonnumeric, null, or non-finite ``x`` and ``y`` coordinates before
Datashader can silently omit them. ``aggregate_points`` uses fixed horizontal
and vertical ranges, fixed output dimensions, and ``datashader.count()`` so
duplicate points remain visible in the aggregate. ``render_points`` applies
one fixed linear color map, making repeated rendering deterministic.

``save_plot`` creates missing destination directories and writes a PNG through
Pillow. The guarded demonstration writes ``datashader_plot.png`` beside the
solution; generated images are not repository artifacts.

Dependencies
------------

Python 3.10 or newer is required. The repository's ``scientific`` dependency
group supplies the pandas, Datashader, and Pillow runtime tools. The ``dev``
dependency group supplies pytest. All input data is committed locally;
execution needs no network service.

Run
---

Run the guarded demonstration from the repository root:

.. code-block:: console

   $ uv run --group scientific python -m CH_15_scientific_python.exercise_01.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run --group scientific pytest CH_15_scientific_python/exercise_01/test_solution_00.py -vv

Reference
---------

The implementation is informed by the chapter's immutable
`Datashader notebook
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_15_scientific_python/T_17_datashader.ipynb>`_.
The upstream material is MIT licensed; this exercise solution is
self-contained.
