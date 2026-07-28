from collections.abc import Callable, MutableMapping
from functools import wraps
from types import FunctionType
from typing import ParamSpec, Protocol, TypeAlias, TypeVar, cast

Method: TypeAlias = Callable[..., object]

Parameters = ParamSpec("Parameters")
ReturnValue = TypeVar("ReturnValue")


class _ClassMethodDescriptor(Protocol):
    @property
    def __func__(self) -> Method: ...


def _wrap_namespace(
    namespace: MutableMapping[str, object],
    wrapper: Callable[[Method], Method] | None,
) -> None:
    """Wrap direct public methods in a prepared class namespace."""
    if wrapper is None:
        return

    namespace_items: list[tuple[str, object]] = list(namespace.items())
    for attribute_name, attribute in namespace_items:
        if attribute_name.startswith("__") and attribute_name.endswith("__"):
            continue
        if isinstance(attribute, FunctionType):
            namespace[attribute_name] = wrapper(attribute)
        elif isinstance(attribute, staticmethod):
            static_method: Method = cast(Method, attribute.__func__)
            namespace[attribute_name] = staticmethod(wrapper(static_method))
        elif isinstance(attribute, classmethod):
            descriptor: _ClassMethodDescriptor = cast(
                _ClassMethodDescriptor,
                attribute,
            )
            namespace[attribute_name] = classmethod(
                wrapper(descriptor.__func__),
            )


class WrappingMeta(type):
    """Wrap methods defined directly in a class namespace."""

    @classmethod
    def __prepare__(
        mcls: type["WrappingMeta"],
        name: str,
        bases: tuple[type, ...],
        /,
        *,
        wrapper: Callable[[Method], Method] | None = None,
        **kwargs: object,
    ) -> MutableMapping[str, object]:
        """Consume wrapper before preparing a class namespace cooperatively."""
        return super().__prepare__(name, bases, **kwargs)

    def __new__(
        cls: type["WrappingMeta"],
        name: str,
        bases: tuple[type, ...],
        namespace: MutableMapping[str, object],
        *,
        wrapper: Callable[[Method], Method] | None = None,
        **kwargs: object,
    ) -> "WrappingMeta":
        """Create a class after wrapping its direct public methods."""
        _wrap_namespace(namespace, wrapper)
        class_namespace: dict[str, object] = cast(dict[str, object], namespace)
        return super().__new__(cls, name, bases, class_namespace, **kwargs)

    def __init__(
        self,
        name: str,
        bases: tuple[type, ...],
        namespace: MutableMapping[str, object],
        *,
        wrapper: Callable[[Method], Method] | None = None,
        **kwargs: object,
    ) -> None:
        """Consume the wrapper keyword and initialize cooperatively."""
        class_namespace: dict[str, object] = cast(dict[str, object], namespace)
        super().__init__(name, bases, class_namespace, **kwargs)


def print_call(
    method: Callable[Parameters, ReturnValue],
) -> Callable[Parameters, ReturnValue]:
    """Print a method name immediately before calling it."""

    @wraps(method)
    def wrapped(
        *args: Parameters.args,
        **kwargs: Parameters.kwargs,
    ) -> ReturnValue:
        print(f"calling {method.__name__}")
        return method(*args, **kwargs)

    return wrapped


class SomeClass(metaclass=WrappingMeta, wrapper=print_call):
    """Demonstrate automatic method decoration."""

    def some_method(self) -> None:
        """Print the demonstration method result."""
        print("some_method() called")


def main() -> None:
    """Run the method-wrapping demonstration."""
    SomeClass().some_method()


if __name__ == "__main__":
    main()
