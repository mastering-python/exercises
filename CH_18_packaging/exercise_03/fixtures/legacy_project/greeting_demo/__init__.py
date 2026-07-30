"""Tiny package used by the legacy-project migration fixture."""

from __future__ import annotations

__version__: str = "1.2.3"


def greeting(name: str) -> str:
    """Return a deterministic greeting."""

    return f"Hello, {name}!"


def main() -> None:
    """Print the console-script greeting."""

    print(greeting("packaging"))
