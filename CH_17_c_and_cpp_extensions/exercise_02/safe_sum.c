#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <limits.h>

static PyObject *
custom_sum(PyObject *self, PyObject *argument)
{
    PyObject *sequence = NULL;
    Py_ssize_t length = 0;
    Py_ssize_t index = 0;
    long long total = 0;

    (void)self;
    sequence = PySequence_Fast(
        argument,
        "custom_sum requires a sequence of integers"
    );
    if (sequence == NULL) {
        return NULL;
    }

    length = PySequence_Fast_GET_SIZE(sequence);
    for (index = 0; index < length; index++) {
        PyObject *item = PySequence_Fast_GET_ITEM(sequence, index);
        long long value = 0;

        if (PyBool_Check(item)) {
            PyErr_SetString(PyExc_TypeError, "custom_sum rejects booleans");
            Py_DECREF(sequence);
            return NULL;
        }
        value = PyLong_AsLongLong(item);
        if (value == -1 && PyErr_Occurred()) {
            Py_DECREF(sequence);
            return NULL;
        }
        if (value > 0 && total > LLONG_MAX - value) {
            PyErr_SetString(
                PyExc_OverflowError,
                "custom_sum cumulative overflow"
            );
            Py_DECREF(sequence);
            return NULL;
        }
        if (value < 0 && total < LLONG_MIN - value) {
            PyErr_SetString(
                PyExc_OverflowError,
                "custom_sum cumulative underflow"
            );
            Py_DECREF(sequence);
            return NULL;
        }
        total += value;
    }

    Py_DECREF(sequence);
    return PyLong_FromLongLong(total);
}

static PyMethodDef module_methods[] = {
    {
        "custom_sum",
        custom_sum,
        METH_O,
        PyDoc_STR("Return a checked signed-64-bit sum.")
    },
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module_definition = {
    PyModuleDef_HEAD_INIT,
    "_safe_sum",
    NULL,
    -1,
    module_methods
};

PyMODINIT_FUNC
PyInit__safe_sum(void)
{
    return PyModule_Create(&module_definition);
}
