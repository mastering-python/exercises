"""Group values into reusable lists."""

from collections.abc import Callable, Hashable, Iterable
from typing import TypeVar, overload

H = TypeVar("H", bound=Hashable)
K = TypeVar("K", bound=Hashable)
T = TypeVar("T")


@overload
def groupby(iterable: Iterable[H], key: None = None) -> dict[H, list[H]]: ...


@overload
def groupby(iterable: Iterable[T], key: Callable[[T], K]) -> dict[K, list[T]]: ...


def groupby(
    iterable: Iterable[T], key: Callable[[T], K] | None = None
) -> dict[K, list[T]] | dict[T, list[T]]:
    """Return input items collected into lists by their group key."""
    if key is not None and not callable(key):
        raise TypeError("key must be callable or None")

    item: T
    if key is None:
        identity_groups: dict[T, list[T]] = {}
        for item in iterable:
            identity_groups.setdefault(item, []).append(item)
        return identity_groups

    keyed_groups: dict[K, list[T]] = {}
    for item in iterable:
        group_key: K = key(item)
        keyed_groups.setdefault(group_key, []).append(item)
    return keyed_groups


def main() -> None:
    """Print a small identity-grouping demonstration."""
    print(groupby("ABACA"))


if __name__ == "__main__":
    main()
