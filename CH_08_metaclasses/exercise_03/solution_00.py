from collections.abc import Callable, Mapping
from functools import wraps
from types import FunctionType
from typing import ParamSpec, Protocol, TypeAlias, TypeVar, cast

Method: TypeAlias = Callable[..., object]

Parameters = ParamSpec("Parameters")
ReturnValue = TypeVar("ReturnValue")


class _ClassMethodDescriptor(Protocol):
    @property
    def __func__(self) -> Method:
        ...


def _wrapped_namespace(
    namespace: Mapping[str, object],
    wrapper: Callable[[Method], Method] | None,
) -> dict[str, object]:
    """Return a class namespace with its direct public methods wrapped."""
    wrapped_namespace: dict[str, object] = dict(namespace)
    if wrapper is None:
        return wrapped_namespace

    for attribute_name, attribute in namespace.items():
        if attribute_name.startswith("__") and attribute_name.endswith("__"):
            continue
        if isinstance(attribute, FunctionType):
            wrapped_namespace[attribute_name] = wrapper(attribute)
        elif isinstance(attribute, staticmethod):
            static_method: Method = cast(Method, attribute.__func__)
            wrapped_namespace[attribute_name] = staticmethod(wrapper(static_method))
        elif isinstance(attribute, classmethod):
            descriptor: _ClassMethodDescriptor = cast(
                _ClassMethodDescriptor,
                attribute,
            )
            wrapped_namespace[attribute_name] = classmethod(
                wrapper(descriptor.__func__),
            )

    return wrapped_namespace


class WrappingMeta(type):
    """Wrap methods defined directly in a class namespace."""

    def __new__(
        cls: type["WrappingMeta"],
        name: str,
        bases: tuple[type, ...],
        namespace: Mapping[str, object],
        *,
        wrapper: Callable[[Method], Method] | None = None,
        **kwargs: object,
    ) -> "WrappingMeta":
        """Create a class after wrapping its direct public methods."""
        return super().__new__(
            cls,
            name,
            bases,
            _wrapped_namespace(namespace, wrapper),
            **kwargs,
        )

    def __init__(
        self,
        name: str,
        bases: tuple[type, ...],
        namespace: Mapping[str, object],
        *,
        wrapper: Callable[[Method], Method] | None = None,
        **kwargs: object,
    ) -> None:
        """Consume the wrapper keyword and initialize cooperatively."""
        super().__init__(name, bases, dict(namespace), **kwargs)


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
