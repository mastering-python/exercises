"""A cached-property descriptor whose value can be deleted and recalculated."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar, cast, overload

__all__: list[str] = ["CachedProperty"]

T = TypeVar("T")
R = TypeVar("R")


class CachedProperty(Generic[T, R]):
    """Cache a computed value in each instance until that value is deleted."""

    func: Callable[[T], R]
    attrname: str | None
    __name__: str
    __qualname__: str
    __module__: str
    __doc__: str | None
    __annotations__: dict[str, object]
    __wrapped__: Callable[[T], R]

    def __init__(self, func: Callable[[T], R]) -> None:
        self.__dict__.update(vars(func))
        self.func = func
        self.attrname = None
        self.__name__ = func.__name__
        self.__qualname__ = func.__qualname__
        self.__module__ = func.__module__
        self.__doc__ = func.__doc__
        self.__annotations__ = func.__annotations__
        self.__wrapped__ = func

    def __set_name__(self, owner: type[T], name: str) -> None:
        if self.attrname is None:
            self.attrname = name
            return
        if name != self.attrname:
            raise TypeError(
                "Cannot assign the same CachedProperty to two different names "
                f"({self.attrname!r} and {name!r})."
            )

    def _bound_name(self) -> str:
        name: str | None = self.attrname
        if name is None:
            raise TypeError("CachedProperty has not been assigned to a class attribute")
        return name

    @overload
    def __get__(
        self,
        instance: None,
        owner: type[T] | None = None,
    ) -> CachedProperty[T, R]: ...

    @overload
    def __get__(self, instance: T, owner: type[T] | None = None) -> R: ...

    def __get__(
        self,
        instance: T | None,
        owner: type[T] | None = None,
    ) -> CachedProperty[T, R] | R:
        name: str = self._bound_name()
        if instance is None:
            return self

        storage: dict[str, object] = self._instance_storage(instance, name)
        if name in storage:
            return cast(R, storage[name])

        value: R = self.func(instance)
        storage[name] = value
        return value

    def __delete__(self, instance: T) -> None:
        name: str = self._bound_name()
        storage: dict[str, object] = self._instance_storage(instance, name)
        try:
            del storage[name]
        except KeyError:
            raise AttributeError(name) from None

    @staticmethod
    def _instance_storage(instance: T, name: str) -> dict[str, object]:
        try:
            return vars(instance)
        except TypeError:
            raise TypeError(
                f"CachedProperty {name!r} requires instances with a __dict__"
            ) from None
