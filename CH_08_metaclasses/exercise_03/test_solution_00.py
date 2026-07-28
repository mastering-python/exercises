import inspect
import subprocess
import sys
from collections.abc import Callable, Mapping
from typing import ClassVar, Protocol, cast

import pytest

from .solution_00 import Method, SomeClass, WrappingMeta, print_call


class _ClassMethodDescriptor(Protocol):
    @property
    def __func__(self) -> Method: ...


def recording_wrapper(
    calls: list[str],
) -> Callable[[Method], Method]:
    def wrap(method: Method) -> Method:
        calls.append(method.__name__)

        def wrapped(*args: object, **kwargs: object) -> object:
            return method(*args, **kwargs)

        return wrapped

    return wrap


def test_instance_static_and_class_methods_are_wrapped_once() -> None:
    calls: list[str] = []

    class Example(
        metaclass=WrappingMeta,
        wrapper=recording_wrapper(calls),
    ):
        def instance_method(self, value: int) -> tuple[str, int]:
            return ("instance", value)

        @staticmethod
        def static_method(value: int) -> tuple[str, int]:
            return ("static", value)

        @classmethod
        def class_method(cls, value: int) -> tuple[str, type["Example"], int]:
            return ("class", cls, value)

    assert calls == ["instance_method", "static_method", "class_method"]
    assert Example().instance_method(1) == ("instance", 1)
    assert Example.static_method(2) == ("static", 2)
    assert Example.class_method(3) == ("class", Example, 3)
    assert calls == ["instance_method", "static_method", "class_method"]


def test_static_and_class_method_descriptors_are_reconstructed() -> None:
    class Example(metaclass=WrappingMeta, wrapper=print_call):
        @staticmethod
        def static_method() -> str:
            return "static"

        @classmethod
        def class_method(cls) -> type["Example"]:
            return cls

    static_descriptor: object = Example.__dict__["static_method"]
    class_descriptor: object = Example.__dict__["class_method"]

    assert isinstance(static_descriptor, staticmethod)
    assert isinstance(class_descriptor, classmethod)
    static_function: Method = cast(Method, static_descriptor.__func__)
    typed_class_descriptor: _ClassMethodDescriptor = cast(
        _ClassMethodDescriptor,
        class_descriptor,
    )
    class_function: Method = typed_class_descriptor.__func__
    assert static_function.__name__ == "static_method"
    assert class_function.__name__ == "class_method"
    assert Example.static_method() == "static"
    assert Example.class_method() is Example


def test_data_properties_other_descriptors_and_dunders_are_untouched() -> None:
    calls: list[str] = []

    class CallableDescriptor:
        def __call__(self) -> str:
            return "descriptor"

        def __get__(self, instance: object, owner: type[object]) -> str:
            return owner.__name__

    descriptor: CallableDescriptor = CallableDescriptor()

    class Example(
        metaclass=WrappingMeta,
        wrapper=recording_wrapper(calls),
    ):
        value: int = 7
        custom: ClassVar[CallableDescriptor] = descriptor

        def __init__(self) -> None:
            self.created: bool = True

        @property
        def label(self) -> str:
            return "property"

        def ordinary(self) -> str:
            return "ordinary"

    example: Example = Example()

    assert calls == ["ordinary"]
    assert Example.value == 7
    assert Example.__dict__["custom"] is descriptor
    assert Example.custom == "Example"
    assert Example.__dict__["label"].fget is not None
    assert Example.__dict__["label"].fget.__name__ == "label"
    assert example.label == "property"
    assert example.created is True
    assert example.ordinary() == "ordinary"


def test_inherited_methods_are_not_wrapped() -> None:
    calls: list[str] = []

    class Parent:
        def inherited(self) -> str:
            return "parent"

    class Child(
        Parent,
        metaclass=WrappingMeta,
        wrapper=recording_wrapper(calls),
    ):
        def direct(self) -> str:
            return "child"

    child: Child = Child()

    assert calls == ["direct"]
    assert child.inherited() == "parent"
    assert child.direct() == "child"


def test_missing_wrapper_leaves_methods_unchanged() -> None:
    class Example(metaclass=WrappingMeta):
        def method(self) -> str:
            return "unchanged"

    original_method: object = Example.__dict__["method"]

    assert Example().method() == "unchanged"
    assert original_method is Example.__dict__["method"]


def test_none_wrapper_leaves_methods_unchanged() -> None:
    class Example(metaclass=WrappingMeta, wrapper=None):
        def method(self) -> str:
            return "unchanged"

    assert Example().method() == "unchanged"


def test_wrapper_keyword_is_consumed_and_other_keywords_are_forwarded() -> None:
    events: list[tuple[str, object]] = []

    class CooperativeMeta(type):
        def __new__(
            cls: type["CooperativeMeta"],
            name: str,
            bases: tuple[type, ...],
            namespace: Mapping[str, object],
            *,
            marker: object,
            **kwargs: object,
        ) -> "CooperativeMeta":
            events.append(("new", marker))
            return super().__new__(cls, name, bases, dict(namespace), **kwargs)

        def __init__(
            self,
            name: str,
            bases: tuple[type, ...],
            namespace: Mapping[str, object],
            *,
            marker: object,
            **kwargs: object,
        ) -> None:
            events.append(("init", marker))
            super().__init__(name, bases, dict(namespace), **kwargs)

    class CombinedMeta(WrappingMeta, CooperativeMeta):
        pass

    marker: object = object()

    class Example(
        metaclass=CombinedMeta,
        wrapper=print_call,
        marker=marker,
    ):
        def method(self) -> str:
            return "wrapped"

    assert events == [("new", marker), ("init", marker)]
    assert Example().method() == "wrapped"


def test_print_call_preserves_metadata_signature_result_and_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    def add(left: int, right: int = 1) -> int:
        """Add two integers."""
        return left + right

    wrapped: Callable[..., int] = print_call(add)

    assert wrapped.__name__ == "add"
    assert wrapped.__doc__ == "Add two integers."
    assert inspect.signature(wrapped) == inspect.signature(add)
    assert wrapped(2, right=3) == 5
    assert capsys.readouterr().out == "calling add\n"


def test_public_example_class_uses_print_call(
    capsys: pytest.CaptureFixture[str],
) -> None:
    SomeClass().some_method()

    assert capsys.readouterr().out == "calling some_method\nsome_method() called\n"


def test_module_import_is_silent() -> None:
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_08_metaclasses.exercise_03.solution_00",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout == ""
    assert completed.stderr == ""


def test_module_demo() -> None:
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "CH_08_metaclasses.exercise_03.solution_00",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout == "calling some_method\nsome_method() called\n"
    assert completed.stderr == ""
