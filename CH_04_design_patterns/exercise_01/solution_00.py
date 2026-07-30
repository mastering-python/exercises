from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping
from reprlib import recursive_repr
from typing import Any, Protocol, TypeVar, cast

K = TypeVar("K")
V = TypeVar("V")
S = TypeVar("S", bound="_Comparable")


class _Comparable(Protocol):
    def __lt__(self, other: Any, /) -> bool: ...


def _as_comparable(value: object) -> _Comparable:
    return cast(_Comparable, value)


class SortedDict(MutableMapping[K, V]):
    def __init__(
        self,
        source: Mapping[K, V] | Iterable[tuple[K, V]] = (),
        keyfunc: Callable[[K], S] | None = None,
    ) -> None:
        self._data: dict[K, V] = dict(source)
        self._keyfunc: Callable[[K], _Comparable] = cast(
            Callable[[K], _Comparable],
            _as_comparable if keyfunc is None else keyfunc,
        )

    def __getitem__(self, key: K) -> V:
        return self._data[key]

    def __setitem__(self, key: K, value: V) -> None:
        self._data[key] = value

    def __delitem__(self, key: K) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[K]:
        return iter(sorted(self._data, key=self._keyfunc))

    def __len__(self) -> int:
        return len(self._data)

    @recursive_repr(fillvalue="...")
    def __repr__(self) -> str:
        ordered: dict[K, V] = {key: self._data[key] for key in self}
        return f"{type(self).__name__}({ordered!r})"
