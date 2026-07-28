Exercise 1: native qsort interfaces
===================================

Question
--------

.. code-block:: text

   1. Try to sort a list of numbers using `ctypes`, `CFFI`, and with a native extension. You can use the `qsort` function in `stdlib`.

Answer
------

``qsort_ctypes``, ``qsort_cffi``, and ``qsort_native`` expose the same
non-mutating contract. They accept a sequence containing only integers in the
platform C ``int`` range, reject booleans and other objects before entering C,
and return a new sorted list. Empty sequences are returned safely without
calling C ``qsort``.

The ctypes and CFFI ABI paths load ``qsort`` from the current process, which is
portable across the supported macOS and Linux environments. Their callbacks
compare relationally instead of subtracting, so ``INT_MIN`` and ``INT_MAX``
cannot overflow the comparator. The CPython extension performs its own checked
per-item conversion, frees temporary memory on every path, and builds a Python
list result.

Native compilation uses the repository's ``native`` dependency group. The
shared builder places the extension, object files, and compiler directories
under an explicit temporary build root; tests and the guarded demo never write
compiled artifacts into the repository.

Run
---

Run the guarded demonstration:

.. code-block:: console

   $ uv run --group native python -m CH_17_c_and_cpp_extensions.exercise_01.solution_00

Run the focused tests:

.. code-block:: console

   $ uv run --group native pytest CH_17_c_and_cpp_extensions/exercise_01/test_solution_00.py -vv

Upstream references
-------------------

The immutable upstream references are
`_libc.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_17_c_and_cpp_extensions/_libc.py>`_,
`T_04_cffi.rst
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_17_c_and_cpp_extensions/T_04_cffi.rst>`_,
`T_05_cffi_open_library.rst
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_17_c_and_cpp_extensions/T_05_cffi_open_library.rst>`_,
and
`T_09_native/setup.py
<https://github.com/mastering-python/code_2/blob/a012f6ce3f5bf11f5bf380d1c4e7f743355adb89/CH_17_c_and_cpp_extensions/T_09_native/setup.py>`_.
The upstream repository is MIT licensed. This solution is self-contained and
does not copy or import those source files at runtime.
