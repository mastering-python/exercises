"""A cached-property descriptor whose value can be deleted and recalculated."""

from __future__ import annotations

from collections.abc import Callable
from types import BuiltinFunctionType, FunctionType, MethodType
from typing import Generic, TypeVar, cast, overload

__all__: list[str] = ["CachedProperty"]

T = TypeVar("T")
R = TypeVar("R")
_MISSING: object = object()
_RESERVED_CUSTOM_ATTRIBUTES: frozenset[str] = frozenset({"function", "name"})


class CachedProperty(Generic[T, R]):
    """Cache a computed value in each instance until that value is deleted."""

    function: Callable[[T], R]
    name: str | None
    __name__: str
    __qualname__: str
    __module__: str
    __doc__: str | None
    __annotations__: dict[str, object]
    __type_params__: tuple[object, ...]
    __wrapped__: Callable[[T], R]

    def __init__(self, function: Callable[[T], R]) -> None:
        self.function = function
        self.name = None
        self._initialize_metadata(function)
        self._copy_metadata(function)
        self._copy_custom_metadata(function)

    def __set_name__(self, owner: type[T], name: str) -> None:
        if self.name is None:
            self.name = name
            return
        if name != self.name:
            raise TypeError(
                "Cannot assign the same CachedProperty to two different names "
                f"({self.name!r} and {name!r})."
            )

    def _bound_name(self) -> str:
        name: str | None = self.name
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

        value: R = self.function(instance)
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

    def _initialize_metadata(self, function: Callable[[T], R]) -> None:
        function_type: type[object] = type(function)

        module: object = self._metadata_value(function_type, "__module__")
        self.__module__ = module if isinstance(module, str) else ""

        name: object = self._metadata_value(function_type, "__name__")
        self.__name__ = name if isinstance(name, str) else "callable"

        qualname: object = self._metadata_value(function_type, "__qualname__")
        self.__qualname__ = qualname if isinstance(qualname, str) else self.__name__

        self.__doc__ = None
        self.__annotations__ = {}
        self.__type_params__ = ()
        self.__wrapped__ = function

    def _copy_metadata(self, function: Callable[[T], R]) -> None:
        module: object = self._callable_metadata_value(function, "__module__")
        if isinstance(module, str):
            self.__module__ = module

        name: object = self._callable_metadata_value(function, "__name__")
        if isinstance(name, str):
            self.__name__ = name

        qualname: object = self._callable_metadata_value(function, "__qualname__")
        if isinstance(qualname, str):
            self.__qualname__ = qualname

        doc: object = self._callable_metadata_value(function, "__doc__")
        if doc is None or isinstance(doc, str):
            self.__doc__ = doc

        annotations: object = self._callable_metadata_value(
            function,
            "__annotations__",
        )
        if type(annotations) is dict:
            annotation_items: dict[object, object] = cast(
                dict[object, object],
                annotations,
            )
            if all(isinstance(key, str) for key in annotation_items):
                self.__annotations__ = cast(dict[str, object], annotation_items)

        type_parameters: object = self._callable_metadata_value(
            function,
            "__type_params__",
        )
        if isinstance(type_parameters, tuple):
            self.__type_params__ = type_parameters

    def _copy_custom_metadata(self, function: Callable[[T], R]) -> None:
        attributes: dict[object, object] | None = self._callable_attributes(function)
        if attributes is None:
            return

        for name, value in attributes.items():
            if (
                isinstance(name, str)
                and not name.startswith("_")
                and name not in _RESERVED_CUSTOM_ATTRIBUTES
            ):
                setattr(self, name, value)

    def _callable_metadata_value(
        self,
        function: Callable[[T], R],
        attribute: str,
    ) -> object:
        if isinstance(
            function,
            (BuiltinFunctionType, FunctionType, MethodType, type),
        ):
            return self._metadata_value(function, attribute)

        attributes: dict[object, object] | None = self._callable_attributes(function)
        if attributes is None:
            return _MISSING
        return attributes.get(attribute, _MISSING)

    def _callable_attributes(
        self,
        function: Callable[[T], R],
    ) -> dict[object, object] | None:
        attributes: object = self._metadata_value(function, "__dict__")
        if type(attributes) is not dict:
            return None
        return cast(dict[object, object], attributes)

    @staticmethod
    def _metadata_value(source: object, attribute: str) -> object:
        try:
            return getattr(source, attribute)
        except Exception:
            return _MISSING
