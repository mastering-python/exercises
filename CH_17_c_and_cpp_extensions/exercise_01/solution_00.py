"""Sort C integers through ctypes, CFFI, and a CPython extension."""

from __future__ import annotations

import ctypes
from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any, cast

from cffi import FFI  # type: ignore[import-untyped]

from CH_17_c_and_cpp_extensions.native_build import build_extension

_C_INT_BITS: int = ctypes.sizeof(ctypes.c_int) * 8
_C_INT_MIN: int = -(1 << (_C_INT_BITS - 1))
_C_INT_MAX: int = (1 << (_C_INT_BITS - 1)) - 1


def _validated_ints(values: Sequence[object]) -> list[int]:
    """Return values proven safe for conversion to C ``int``."""
    checked: list[int] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("qsort accepts integers, not booleans or other values")
        if value < _C_INT_MIN or value > _C_INT_MAX:
            raise OverflowError("value is outside C int range")
        checked.append(value)
    return checked


def qsort_ctypes(values: Sequence[int]) -> list[int]:
    """Sort C-int values through process libc and return a new list."""
    checked: list[int] = _validated_ints(values)
    if not checked:
        return []

    comparator_type = ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )

    def compare(left_address: int, right_address: int) -> int:
        left_pointer = ctypes.cast(left_address, ctypes.POINTER(ctypes.c_int))
        right_pointer = ctypes.cast(right_address, ctypes.POINTER(ctypes.c_int))
        left_value: int = left_pointer.contents.value
        right_value: int = right_pointer.contents.value
        return (left_value > right_value) - (left_value < right_value)

    compare_callback = comparator_type(compare)
    array_type = ctypes.c_int * len(checked)
    data = array_type(*checked)
    libc: ctypes.CDLL = ctypes.CDLL(None)
    qsort = libc.qsort
    qsort.argtypes = [
        ctypes.c_void_p,
        ctypes.c_size_t,
        ctypes.c_size_t,
        comparator_type,
    ]
    qsort.restype = None
    qsort(data, len(checked), ctypes.sizeof(ctypes.c_int), compare_callback)
    return list(data)


def qsort_cffi(values: Sequence[int]) -> list[int]:
    """Sort C-int values through CFFI ABI mode and return a new list."""
    checked: list[int] = _validated_ints(values)
    if not checked:
        return []

    ffi: FFI = FFI()
    ffi.cdef("void qsort(void *, size_t, size_t, int (*)(const void *, const void *));")
    libc: Any = ffi.dlopen(None)
    data: Any = ffi.new("int[]", checked)

    def compare(left: object, right: object) -> int:
        left_pointer: Any = ffi.cast("const int *", cast(Any, left))
        right_pointer: Any = ffi.cast("const int *", cast(Any, right))
        left_value: int = left_pointer[0]
        right_value: int = right_pointer[0]
        return (left_value > right_value) - (left_value < right_value)

    compare_callback: Any = ffi.callback("int(const void *, const void *)")(compare)
    libc.qsort(data, len(checked), ffi.sizeof("int"), compare_callback)
    return [int(data[index]) for index in range(len(checked))]


def qsort_native(
    values: Sequence[int],
    *,
    native_module: ModuleType,
) -> list[int]:
    """Sort C-int values with a compiled CPython extension."""
    checked: list[int] = _validated_ints(values)
    result: object = native_module.sort_ints(checked)
    if not isinstance(result, list):
        raise TypeError("native qsort returned a non-integer list")
    result_items: list[object] = cast(list[object], result)
    typed_result: list[int] = []
    for value in result_items:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("native qsort returned a non-integer list")
        typed_result.append(value)
    return typed_result


def main() -> None:
    """Demonstrate all paths without leaving compiler output in the repository."""
    values: list[int] = [3, -1, 2]
    print(qsort_ctypes(values))
    print(qsort_cffi(values))
    with TemporaryDirectory(prefix="mastering-python-qsort-") as directory:
        build_root: Path = Path(directory)
        source: Path = Path(__file__).with_name("native_qsort.c")
        native_module: ModuleType = build_extension(
            "_native_qsort",
            source,
            build_root,
        )
        print(qsort_native(values, native_module=native_module))


if __name__ == "__main__":
    main()
