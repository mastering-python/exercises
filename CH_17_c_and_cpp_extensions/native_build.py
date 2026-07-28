"""Build and import CPython extensions inside an explicit build root."""

from __future__ import annotations

import errno
import importlib.util
from pathlib import Path
from types import ModuleType

from setuptools import Distribution, Extension  # type: ignore[import-untyped]
from setuptools.command.build_ext import build_ext  # type: ignore[import-untyped]


def build_extension(
    module_name: str,
    source: Path,
    build_root: Path,
) -> ModuleType:
    """Compile *source* under *build_root* and import *module_name*."""
    if not source.is_file():
        raise FileNotFoundError(
            errno.ENOENT,
            "native extension source is not a file",
            str(source),
        )

    source_path: Path = source.resolve()
    root: Path = build_root.resolve()
    build_lib: Path = root / "lib"
    build_temp: Path = root / "temp"
    build_lib.mkdir(parents=True, exist_ok=True)
    build_temp.mkdir(parents=True, exist_ok=True)

    extension: Extension = Extension(module_name, sources=[str(source_path)])
    distribution: Distribution = Distribution(
        {
            "name": module_name,
            "ext_modules": [extension],
        }
    )
    command: build_ext = build_ext(distribution)
    command.ensure_finalized()
    command.inplace = False
    command.build_lib = str(build_lib)
    command.build_temp = str(build_temp)
    command.run()

    extension_path: Path = Path(command.get_ext_fullpath(module_name)).resolve()
    if not extension_path.is_relative_to(root):
        raise RuntimeError(f"compiler output escaped build root: {extension_path}")
    if not extension_path.is_file():
        raise RuntimeError(
            f"compiler did not produce expected extension: {extension_path}"
        )

    spec = importlib.util.spec_from_file_location(module_name, extension_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load extension at {extension_path}")
    module: ModuleType = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
