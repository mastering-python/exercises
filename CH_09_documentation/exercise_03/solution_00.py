"""Count nodes in recursively typed trees."""

from __future__ import annotations

from typing import TypeAlias

Tree: TypeAlias = dict[str, "Tree"]


def count_nodes(tree: Tree) -> int:
    """Count named nodes with iterative cycle detection and memoization."""
    active: set[int] = set()
    completed: dict[int, int] = {}
    stack: list[tuple[Tree, tuple[Tree, ...] | None]] = [(tree, None)]

    while stack:
        current, children = stack.pop()
        identity: int = id(current)

        if children is not None:
            total: int = 0
            child: Tree
            for child in children:
                total += 1 + completed[id(child)]
            completed[identity] = total
            active.remove(identity)
            continue

        if identity in completed:
            continue
        if identity in active:
            raise ValueError("tree contains cycle")

        active.add(identity)
        current_children: tuple[Tree, ...] = tuple(current.values())
        stack.append((current, current_children))
        pending_child: Tree
        for pending_child in reversed(current_children):
            stack.append((pending_child, None))

    return completed[id(tree)]


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
