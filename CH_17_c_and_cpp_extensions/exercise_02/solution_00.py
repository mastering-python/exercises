"""Sum integers in a checked CPython extension."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from tempfile import TemporaryDirectory
from types import ModuleType

from CH_17_c_and_cpp_extensions.native_build import build_extension


def _validated_ints(values: Sequence[object]) -> list[int]:
    """Return integer values while rejecting booleans and other objects."""
    checked: list[int] = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("custom_sum accepts integers, not booleans or other values")
        checked.append(value)
    return checked


def custom_sum(
    values: Sequence[int],
    *,
    native_module: ModuleType,
) -> int:
    """Return a checked native signed-64-bit sum."""
    checked: list[int] = _validated_ints(values)
    result: object = native_module.custom_sum(checked)
    if isinstance(result, bool) or not isinstance(result, int):
        raise TypeError("native custom_sum returned a non-integer")
    return result


def main() -> None:
    """Compile and run the demonstration entirely in a temporary directory."""
    with TemporaryDirectory(prefix="mastering-python-safe-sum-") as directory:
        build_root: Path = Path(directory)
        source: Path = Path(__file__).with_name("safe_sum.c")
        native_module: ModuleType = build_extension(
            "_safe_sum",
            source,
            build_root,
        )
        print(custom_sum([1, 2, 3], native_module=native_module))


if __name__ == "__main__":
    main()
