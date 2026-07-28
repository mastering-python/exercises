import subprocess
import sys
from typing import ClassVar

import pytest

from .solution_00 import ExpectedBasesMeta, SomeBaseClass, Trade


def test_trade_directly_inherits_expected_base() -> None:
    trade: Trade = Trade()

    assert issubclass(Trade, SomeBaseClass)
    assert isinstance(trade, SomeBaseClass)


def test_direct_inheritance_satisfies_requirement() -> None:
    class RequiredBase:
        pass

    class Complete(
        RequiredBase,
        metaclass=ExpectedBasesMeta,
        expected_bases=(RequiredBase,),
    ):
        pass

    assert issubclass(Complete, RequiredBase)


def test_multiple_levels_of_indirect_inheritance_satisfy_requirement() -> None:
    class RequiredBase:
        pass

    class Grandparent(RequiredBase):
        pass

    class Parent(Grandparent):
        pass

    class Complete(
        Parent,
        metaclass=ExpectedBasesMeta,
        expected_bases=(RequiredBase,),
    ):
        pass

    assert issubclass(Complete, RequiredBase)


def test_requirement_inherited_through_mixin_satisfies_requirement() -> None:
    class RequiredBase:
        pass

    class RequiredMixin(RequiredBase):
        pass

    class UnrelatedBase:
        pass

    class Complete(
        UnrelatedBase,
        RequiredMixin,
        metaclass=ExpectedBasesMeta,
        expected_bases=(RequiredBase,),
    ):
        pass

    assert issubclass(Complete, RequiredBase)


def test_empty_requirements_allow_plain_class() -> None:
    class Plain(metaclass=ExpectedBasesMeta):
        value: int = 7

    assert Plain.value == 7


def test_one_missing_base_reports_class_and_base_name() -> None:
    class RequiredBase:
        pass

    with pytest.raises(TypeError) as error:

        class Broken(
            metaclass=ExpectedBasesMeta,
            expected_bases=(RequiredBase,),
        ):
            pass

        _ = Broken

    assert str(error.value) == "Broken must inherit RequiredBase"


def test_multiple_missing_bases_are_aggregated_in_requested_order() -> None:
    class PresentBase:
        pass

    class FirstMissingBase:
        pass

    class SecondMissingBase:
        pass

    with pytest.raises(TypeError) as error:

        class Broken(
            PresentBase,
            metaclass=ExpectedBasesMeta,
            expected_bases=(
                FirstMissingBase,
                PresentBase,
                SecondMissingBase,
            ),
        ):
            pass

        _ = Broken

    assert str(error.value) == "Broken must inherit FirstMissingBase, SecondMissingBase"


def test_expected_bases_keyword_is_consumed() -> None:
    class KeywordAware:
        received_keywords: ClassVar[dict[str, object] | None] = None

        def __init_subclass__(cls, **kwargs: object) -> None:
            super().__init_subclass__()
            cls.received_keywords = dict(kwargs)

    class Complete(
        KeywordAware,
        metaclass=ExpectedBasesMeta,
        expected_bases=(KeywordAware,),
    ):
        pass

    assert Complete.received_keywords == {}


def test_unrelated_class_keyword_is_forwarded_to_keyword_only_hook() -> None:
    class KeywordAware:
        received_marker: ClassVar[str | None] = None

        def __init_subclass__(cls, *, marker: str) -> None:
            super().__init_subclass__()
            cls.received_marker = marker

    class Complete(
        KeywordAware,
        metaclass=ExpectedBasesMeta,
        expected_bases=(KeywordAware,),
        marker="forwarded",
    ):
        pass

    assert Complete.received_marker == "forwarded"


def test_module_import_is_silent() -> None:
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-c",
            "import CH_08_metaclasses.exercise_02.solution_00",
        ],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_module_demo() -> None:
    completed: subprocess.CompletedProcess[str] = subprocess.run(
        [
            sys.executable,
            "-m",
            "CH_08_metaclasses.exercise_02.solution_00",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert completed.stdout == "True\n"
    assert completed.stderr == ""
