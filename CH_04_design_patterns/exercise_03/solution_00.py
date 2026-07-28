from __future__ import annotations

from typing import Any, ClassVar, TypeVar, cast

_BorgT = TypeVar("_BorgT", bound="Borg")


class Borg:
    """Share attribute state between instances of each exact class."""

    _state: ClassVar[dict[str, object]] = {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls._state = {}

    def __new__(cls: type[_BorgT], *args: Any, **kwargs: Any) -> _BorgT:
        del args, kwargs
        borg_type: type[Borg] = cast(type[Borg], cls)
        instance: _BorgT = cast(_BorgT, object.__new__(borg_type))
        instance.__dict__ = cls._state
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
