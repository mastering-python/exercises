from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar, TypeVar, cast

_BorgT = TypeVar("_BorgT", bound="Borg")


class Borg:
    """Share attribute state between instances of each exact class."""

    _shared_state: ClassVar[dict[str, object]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls._shared_state = {}

    def __new__(cls: type[_BorgT], *args: Any, **kwargs: Any) -> _BorgT:
        del args, kwargs
        allocator: Callable[[type[_BorgT]], _BorgT] = cast(
            Callable[[type[_BorgT]], _BorgT], super().__new__
        )
        instance: _BorgT = allocator(cls)
        object.__setattr__(instance, "__dict__", cls._shared_state)
        return instance


def main() -> None:
    class Settings(Borg):
        language: str

    first: Settings = Settings()
    second: Settings = Settings()
    first.language = "Python"

    print(first is second)
    print(second.language)


if __name__ == "__main__":
    main()
