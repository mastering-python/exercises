"""Count nodes in recursively typed trees."""

from __future__ import annotations

from typing import TypeAlias

Tree: TypeAlias = dict[str, "Tree"]


def count_nodes(tree: Tree) -> int:
    """Count named nodes, rejecting cycles on the active recursion path."""
    return _count_nodes(tree, set())


def _count_nodes(tree: Tree, active: set[int]) -> int:
    identity: int = id(tree)
    if identity in active:
        raise ValueError("tree contains cycle")

    active.add(identity)
    total: int = 0
    try:
        subtree: Tree
        for subtree in tree.values():
            total += 1 + _count_nodes(subtree, active)
    finally:
        active.remove(identity)
    return total


def main() -> None:
    """Print the node count for the canonical demonstration tree."""
    tree: Tree = {
        "docs": {
            "api": {},
            "guide": {},
        },
        "src": {
            "package": {
                "module": {},
            },
        },
    }
    print(count_nodes(tree))


if __name__ == "__main__":
    main()
