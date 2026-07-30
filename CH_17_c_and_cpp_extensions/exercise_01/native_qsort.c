#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <limits.h>
#include <stdlib.h>

static int
compare_ints(const void *left_pointer, const void *right_pointer)
{
    const int left = *(const int *)left_pointer;
    const int right = *(const int *)right_pointer;

    return (left > right) - (left < right);
}

static PyObject *
sort_ints(PyObject *self, PyObject *argument)
{
    PyObject *sequence = NULL;
    PyObject *result = NULL;
    int *values = NULL;
    Py_ssize_t length = 0;
    Py_ssize_t index = 0;

    (void)self;
    sequence = PySequence_Fast(
        argument,
        "sort_ints requires a sequence of integers"
    );
    if (sequence == NULL) {
        return NULL;
    }

    length = PySequence_Fast_GET_SIZE(sequence);
    if (length > 0) {
        values = PyMem_New(int, length);
        if (values == NULL) {
            Py_DECREF(sequence);
            return PyErr_NoMemory();
        }
    }

    for (index = 0; index < length; index++) {
        PyObject *item = PySequence_Fast_GET_ITEM(sequence, index);
        long value = 0;

        if (PyBool_Check(item)) {
            PyErr_SetString(PyExc_TypeError, "sort_ints rejects booleans");
            goto error;
        }
        value = PyLong_AsLong(item);
        if (value == -1 && PyErr_Occurred()) {
            goto error;
        }
        if (value < INT_MIN || value > INT_MAX) {
            PyErr_SetString(PyExc_OverflowError, "value is outside C int range");
            goto error;
        }
        values[index] = (int)value;
    }

    if (length > 1) {
        qsort(values, (size_t)length, sizeof(int), compare_ints);
    }

    result = PyList_New(length);
    if (result == NULL) {
        goto error;
    }
    for (index = 0; index < length; index++) {
        PyObject *item = PyLong_FromLong((long)values[index]);

        if (item == NULL) {
            goto error;
        }
        PyList_SET_ITEM(result, index, item);
    }

    PyMem_Free(values);
    Py_DECREF(sequence);
    return result;

error:
    Py_XDECREF(result);
    PyMem_Free(values);
    Py_DECREF(sequence);
    return NULL;
}

static PyMethodDef module_methods[] = {
    {
        "sort_ints",
        sort_ints,
        METH_O,
        PyDoc_STR("Sort a sequence of C-int values.")
    },
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module_definition = {
    PyModuleDef_HEAD_INIT,
    "_native_qsort",
    NULL,
    -1,
    module_methods
};

PyMODINIT_FUNC
PyInit__native_qsort(void)
{
    return PyModule_Create(&module_definition);
}
