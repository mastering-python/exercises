"""Tests for isolated native-extension compilation."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType

import pytest

from CH_17_c_and_cpp_extensions.native_build import build_extension


def test_build_extension_imports_from_temporary_directory(tmp_path: Path) -> None:
    source: Path = tmp_path / "answer.c"
    source.write_text(
        """
#define PY_SSIZE_T_CLEAN
#include <Python.h>

static PyObject *answer(PyObject *self, PyObject *args) {
    return PyLong_FromLong(42);
}

static PyMethodDef methods[] = {
    {"answer", answer, METH_NOARGS, "Return 42."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "_answer",
    NULL,
    -1,
    methods
};

PyMODINIT_FUNC PyInit__answer(void) {
    return PyModule_Create(&module);
}
""".strip(),
        encoding="utf-8",
    )
    build_root: Path = tmp_path / "build"

    module: ModuleType = build_extension("_answer", source, build_root)

    assert module.answer() == 42
    assert module.__file__ is not None
    module_path: Path = Path(module.__file__).resolve()
    assert module_path.is_relative_to(build_root.resolve())


def test_build_extension_rejects_missing_source(tmp_path: Path) -> None:
    missing: Path = tmp_path / "missing.c"

    with pytest.raises(FileNotFoundError) as caught:
        build_extension("_missing", missing, tmp_path / "build")

    assert caught.value.filename == str(missing)
