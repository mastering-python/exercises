"""An AVL-tree-backed sorted collection."""

from collections.abc import Callable, Collection, Iterable, Iterator
from dataclasses import dataclass, field
from reprlib import recursive_repr
from typing import Any, Generic, Protocol, TypeVar, cast

T = TypeVar("T")


class _Comparable(Protocol):
    def __lt__(self, other: Any, /) -> bool:
        """Return whether this value sorts before ``other``."""
        raise NotImplementedError


S = TypeVar("S", bound=_Comparable)


def _identity(value: T) -> T:
    return value


@dataclass(slots=True)
class _Node(Generic[T, S]):
    value: T
    sort_key: S
    duplicates: list[T] = field(default_factory=list[T])
    height: int = 1
    left: "_Node[T, S] | None" = None
    right: "_Node[T, S] | None" = None


class SortedList(Collection[T], Generic[T, S]):
    """Store values in sort-key order in an AVL multiset."""

    def __init__(
        self,
        values: Iterable[T] = (),
        *,
        key: Callable[[T], S] | None = None,
    ) -> None:
        self._root: _Node[T, S] | None = None
        self._key: Callable[[T], S] = (
            cast(Callable[[T], S], _identity) if key is None else key
        )
        self._size: int = 0
        for value in values:
            self.add(value)

    @staticmethod
    def _height(node: _Node[T, S] | None) -> int:
        return 0 if node is None else node.height

    @classmethod
    def _update_height(cls, node: _Node[T, S]) -> None:
        node.height = 1 + max(cls._height(node.left), cls._height(node.right))

    @classmethod
    def _rotate_left(cls, root: _Node[T, S]) -> _Node[T, S]:
        pivot: _Node[T, S] | None = root.right
        if pivot is None:
            raise RuntimeError("left rotation requires a right child")
        root.right = pivot.left
        pivot.left = root
        cls._update_height(root)
        cls._update_height(pivot)
        return pivot

    @classmethod
    def _rotate_right(cls, root: _Node[T, S]) -> _Node[T, S]:
        pivot: _Node[T, S] | None = root.left
        if pivot is None:
            raise RuntimeError("right rotation requires a left child")
        root.left = pivot.right
        pivot.right = root
        cls._update_height(root)
        cls._update_height(pivot)
        return pivot

    @classmethod
    def _rebalance(cls, node: _Node[T, S]) -> _Node[T, S]:
        cls._update_height(node)
        balance: int = cls._height(node.left) - cls._height(node.right)

        if balance > 1:
            left: _Node[T, S] | None = node.left
            if left is None:
                raise RuntimeError("left-heavy node requires a left child")
            if cls._height(left.left) < cls._height(left.right):
                node.left = cls._rotate_left(left)
            return cls._rotate_right(node)

        if balance < -1:
            right: _Node[T, S] | None = node.right
            if right is None:
                raise RuntimeError("right-heavy node requires a right child")
            if cls._height(right.right) < cls._height(right.left):
                node.right = cls._rotate_right(right)
            return cls._rotate_left(node)

        return node

    @classmethod
    def _add_node(cls, node: _Node[T, S] | None, value: T, sort_key: S) -> _Node[T, S]:
        if node is None:
            return _Node(value=value, sort_key=sort_key)

        if sort_key < node.sort_key:
            node.left = cls._add_node(node.left, value, sort_key)
        elif node.sort_key < sort_key:
            node.right = cls._add_node(node.right, value, sort_key)
        else:
            node.duplicates.append(value)
            return node
        return cls._rebalance(node)

    def add(self, value: T) -> None:
        """Insert ``value`` while preserving sorted iteration."""
        sort_key: S = self._key(value)
        self._root = self._add_node(self._root, value, sort_key)
        self._size += 1

    insert = add

    @property
    def tree_height(self) -> int:
        """Return the current AVL height without allowing mutation."""
        return self._height(self._root)

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[T]:
        stack: list[_Node[T, S]] = []
        node: _Node[T, S] | None = self._root
        while stack or node is not None:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            yield node.value
            yield from node.duplicates
            node = node.right

    def __contains__(self, value: object) -> bool:
        node: _Node[T, S] | None = self._root
        if node is None:
            return False
        candidate: T = cast(T, value)
        sort_key: S = self._key(candidate)
        while node is not None:
            if sort_key < node.sort_key:
                node = node.left
            elif node.sort_key < sort_key:
                node = node.right
            else:
                return node.value == value or any(
                    duplicate == value for duplicate in node.duplicates
                )
        return False

    @recursive_repr(fillvalue="...")
    def __repr__(self) -> str:
        return f"{type(self).__name__}({list(self)!r})"


if __name__ == "__main__":
    example: SortedList[int, int] = SortedList([5, 3, 1, 4, 2, 2])
    print(example)
