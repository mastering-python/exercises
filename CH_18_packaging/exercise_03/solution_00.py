"""Safely migrate a constrained legacy setuptools project."""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import cast

SUPPORTED_FIELDS: frozenset[str] = frozenset(
    {"name", "version", "description", "python_requires", "entry_points"}
)
REQUIRED_FIELDS: frozenset[str] = SUPPORTED_FIELDS
SCRIPT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
DISTRIBUTION_NAME_PATTERN: re.Pattern[str] = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$"
)


@dataclass(frozen=True)
class ProjectMetadata:
    """Supported static metadata extracted from one legacy setup call."""

    name: str
    version: str
    description: str
    requires_python: str
    scripts: dict[str, str]


def _is_setup_call(node: ast.Call) -> bool:
    function: ast.expr = node.func
    return (isinstance(function, ast.Name) and function.id == "setup") or (
        isinstance(function, ast.Attribute) and function.attr == "setup"
    )


def _find_setup_call(tree: ast.Module) -> ast.Call:
    calls: list[ast.Call] = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _is_setup_call(node)
    ]
    if len(calls) != 1:
        raise ValueError("setup.py must contain exactly one setup call")
    call: ast.Call = calls[0]
    if call.args:
        raise ValueError("setup metadata must use named static fields")
    return call


def _read_supported_fields(call: ast.Call) -> dict[str, object]:
    values: dict[str, object] = {}
    for keyword in call.keywords:
        if keyword.arg is None:
            raise ValueError("setup keyword expansion is not supported")
        if keyword.arg not in SUPPORTED_FIELDS:
            continue
        if keyword.arg in values:
            raise ValueError(f"duplicate setup field: {keyword.arg}")
        try:
            value: object = ast.literal_eval(keyword.value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{keyword.arg} must be a static literal") from error
        values[keyword.arg] = value
    missing: list[str] = sorted(REQUIRED_FIELDS.difference(values))
    if missing:
        raise ValueError(f"required metadata fields missing: {', '.join(missing)}")
    return values


def _parse_console_scripts(entry_points: object) -> dict[str, str]:
    if not isinstance(entry_points, dict):
        raise ValueError("entry_points must contain a console_scripts mapping")
    groups: dict[object, object] = cast(dict[object, object], entry_points)
    entries: object = groups.get("console_scripts")
    if not isinstance(entries, (list, tuple)):
        raise ValueError("entry_points must contain a console_scripts list")
    script_entries: list[object] | tuple[object, ...] = cast(
        list[object] | tuple[object, ...],
        entries,
    )
    scripts: dict[str, str] = {}
    for entry in script_entries:
        if not isinstance(entry, str) or entry.count("=") != 1:
            raise ValueError("each console script must use name=module:function")
        name, target = (part.strip() for part in entry.split("=", maxsplit=1))
        if (
            SCRIPT_NAME_PATTERN.fullmatch(name) is None
            or target.count(":") != 1
            or any(not part.strip() for part in target.split(":", maxsplit=1))
        ):
            raise ValueError("each console script must use name=module:function")
        if name in scripts:
            raise ValueError(f"duplicate console script: {name}")
        scripts[name] = target
    return scripts


def _required_string(values: dict[str, object], field: str) -> str:
    value: object = values[field]
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty static literal string")
    return value


def read_setup_metadata(setup_py: Path) -> ProjectMetadata:
    """Parse supported metadata without importing or executing ``setup.py``."""

    source: str = setup_py.read_text(encoding="utf-8")
    try:
        tree: ast.Module = ast.parse(source, filename=str(setup_py))
    except SyntaxError as error:
        raise ValueError("setup.py must contain valid Python") from error
    values: dict[str, object] = _read_supported_fields(_find_setup_call(tree))
    return ProjectMetadata(
        name=_required_string(values, "name"),
        version=_required_string(values, "version"),
        description=_required_string(values, "description"),
        requires_python=_required_string(values, "python_requires"),
        scripts=_parse_console_scripts(values["entry_points"]),
    )


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_pyproject(metadata: ProjectMetadata) -> str:
    """Render deterministic TOML using safely quoted basic strings."""

    lines: list[str] = [
        "[build-system]",
        'requires = ["setuptools>=77", "wheel"]',
        'build-backend = "setuptools.build_meta"',
        "",
        "[project]",
        f"name = {_toml_string(metadata.name)}",
        f"version = {_toml_string(metadata.version)}",
        f"description = {_toml_string(metadata.description)}",
        'readme = "README.rst"',
        f"requires-python = {_toml_string(metadata.requires_python)}",
        "",
        "[project.scripts]",
    ]
    lines.extend(
        f"{_toml_string(name)} = {_toml_string(target)}"
        for name, target in sorted(metadata.scripts.items())
    )
    lines.extend(
        [
            "",
            "[tool.setuptools.packages.find]",
            'where = ["src"]',
            "",
        ]
    )
    return "\n".join(lines)


def _resolve_package_source(source: Path, distribution_name: str) -> Path:
    if DISTRIBUTION_NAME_PATTERN.fullmatch(distribution_name) is None:
        raise ValueError(f"invalid distribution name: {distribution_name!r}")
    package_name: str = re.sub(r"[-_.]+", "_", distribution_name)
    source_resolved: Path = source.resolve()
    package_candidate: Path = source_resolved / package_name
    if package_candidate.is_symlink():
        raise ValueError("package root must not be a symlink")
    package_source: Path = package_candidate.resolve()
    try:
        relative: Path = package_source.relative_to(source_resolved)
    except ValueError as error:
        raise ValueError("distribution name must resolve inside source") from error
    if relative.parts != (package_name,) or package_source == source_resolved:
        raise ValueError("distribution name must resolve to one package child")
    if not package_source.is_dir():
        raise FileNotFoundError(package_source)
    return package_source


def _validate_regular_file(path: Path, label: str) -> None:
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symlink")
    if not path.is_file():
        raise FileNotFoundError(path)


def _validate_package_tree(package_source: Path) -> None:
    if package_source.is_symlink():
        raise ValueError("package root must not be a symlink")
    for root, directory_names, file_names in os.walk(
        package_source,
        topdown=True,
        followlinks=False,
    ):
        directory_names.sort()
        file_names.sort()
        root_path: Path = Path(root)
        for name in [*directory_names, *file_names]:
            entry: Path = root_path / name
            if entry.is_symlink():
                raise ValueError(f"package tree contains symlink: {entry}")


def _validate_migration_paths(source: Path, destination: Path) -> tuple[Path, Path]:
    source_resolved: Path = source.resolve()
    destination_resolved: Path = destination.resolve()
    if not source_resolved.is_dir():
        raise FileNotFoundError(source_resolved)
    if destination_resolved == source_resolved or (
        destination_resolved.is_relative_to(source_resolved)
        or source_resolved.is_relative_to(destination_resolved)
    ):
        raise ValueError("source and destination must not contain each other")
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    destination_parent: Path = destination.parent
    if not destination_parent.is_dir():
        raise FileNotFoundError(destination_parent)
    return source_resolved, destination_parent


def _populate_migration(
    temporary: Path,
    package_source: Path,
    readme_source: Path,
    pyproject: str,
) -> None:
    package_destination: Path = temporary / "src" / package_source.name
    package_destination.parent.mkdir()
    shutil.copytree(
        package_source,
        package_destination,
        symlinks=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    _validate_package_tree(package_destination)
    shutil.copy2(readme_source, temporary / "README.rst")
    (temporary / "pyproject.toml").write_text(pyproject, encoding="utf-8")


def migrate_project(source: Path, destination: Path) -> Path:
    """Create a modern src-layout copy without executing or copying setup.py."""

    source_resolved, destination_parent = _validate_migration_paths(
        source,
        destination,
    )
    setup_py: Path = source_resolved / "setup.py"
    _validate_regular_file(setup_py, "setup.py")
    metadata: ProjectMetadata = read_setup_metadata(setup_py)
    package_source: Path = _resolve_package_source(source_resolved, metadata.name)
    _validate_package_tree(package_source)
    readme_source: Path = source_resolved / "README.rst"
    _validate_regular_file(readme_source, "README.rst")
    pyproject: str = render_pyproject(metadata)
    temporary: Path = Path(
        tempfile.mkdtemp(
            prefix=f".{destination.name}.tmp-",
            dir=destination_parent,
        )
    )
    try:
        _populate_migration(temporary, package_source, readme_source, pyproject)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(destination)
        temporary.rename(destination)
    except BaseException:
        shutil.rmtree(temporary)
        raise
    return destination
