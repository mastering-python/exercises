import subprocess
import sys
from typing import ClassVar

import pytest

from .solution_00 import ExpectedAttrsMeta, Trade


def test_trade_exposes_required_methods() -> None:
    trade: Trade = Trade()

    assert trade.buy() == "buy"
    assert trade.sell() == "sell"


def test_direct_methods_and_values_satisfy_requirements() -> None:
    class Complete(
        metaclass=ExpectedAttrsMeta,
        required_attributes=("quantity", "execute"),
    ):
        quantity: int = 3

        def execute(self) -> str:
            return "executed"

    complete: Complete = Complete()

    assert complete.quantity == 3
    assert complete.execute() == "executed"


def test_inherited_attributes_satisfy_requirements() -> None:
    class Parent:
        inherited_value: int = 5

        def inherited_method(self) -> str:
            return "inherited"

    class Child(
        Parent,
        metaclass=ExpectedAttrsMeta,
        required_attributes=("inherited_value", "inherited_method"),
    ):
        pass

    child: Child = Child()

    assert child.inherited_value == 5
    assert child.inherited_method() == "inherited"


def test_indirectly_inherited_attributes_satisfy_requirements() -> None:
    class Grandparent:
        inherited_value: int = 8

    class Parent(Grandparent):
        pass

    class Child(
        Parent,
        metaclass=ExpectedAttrsMeta,
        required_attributes=("inherited_value",),
    ):
        pass

    assert Child.inherited_value == 8


def test_missing_members_are_aggregated_in_requested_order() -> None:
    with pytest.raises(AttributeError) as error:

        class Broken(
            metaclass=ExpectedAttrsMeta,
            required_attributes=("sell", "buy", "quantity"),
        ):
            pass

        _ = Broken

    assert str(error.value) == (
        "Broken missing required attribute(s): sell, buy, quantity"
    )


def test_empty_requirements_allow_plain_class() -> None:
    class Plain(metaclass=ExpectedAttrsMeta):
        value: int = 7

    assert Plain.value == 7


def test_required_attributes_keyword_is_consumed() -> None:
    class KeywordAware:
        received_keywords: ClassVar[dict[str, object] | None] = None

        def __init_subclass__(cls, **kwargs: object) -> None:
            super().__init_subclass__()
            cls.received_keywords = dict(kwargs)

    class Complete(
        KeywordAware,
        metaclass=ExpectedAttrsMeta,
        required_attributes=("value",),
    ):
        value: int = 11

    assert Complete.received_keywords == {}


def test_module_import_is_silent() -> None:
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_08_metaclasses.exercise_01.solution_00",
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
            "CH_08_metaclasses.exercise_01.solution_00",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout == "buy sell\n"
    assert completed.stderr == ""
