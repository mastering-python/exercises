import subprocess
import sys
from collections.abc import Iterator, Mapping
from typing import ClassVar, cast

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


@pytest.mark.parametrize(
    "invalid_expected_bases",
    [
        None,
        [SomeBaseClass],
        (SomeBaseClass, "not-a-type"),
    ],
    ids=["none", "list", "non-type-item"],
)
def test_invalid_requirements_are_rejected_before_class_hook_side_effects(
    invalid_expected_bases: object,
) -> None:
    events: list[str] = []

    class RecordingDescriptor:
        def __set_name__(self, owner: type[object], name: str) -> None:
            events.append(f"set_name:{name}")

    class HookBase:
        def __init_subclass__(cls) -> None:
            events.append("init_subclass")
            super().__init_subclass__()

    with pytest.raises(TypeError) as error:

        class Broken(
            HookBase,
            metaclass=ExpectedBasesMeta,
            expected_bases=cast(
                tuple[type, ...],
                invalid_expected_bases,
            ),
        ):
            descriptor: ClassVar[RecordingDescriptor] = RecordingDescriptor()

        _ = Broken

    assert (
        str(error.value)
        == "Broken expected_bases must be a tuple containing only types"
    )
    assert events == []


def test_missing_base_validation_runs_after_class_construction_hooks() -> None:
    events: list[str] = []

    class RecordingDescriptor:
        def __set_name__(self, owner: type[object], name: str) -> None:
            events.append(f"set_name:{name}")

    class HookBase:
        def __init_subclass__(cls) -> None:
            events.append("init_subclass")
            super().__init_subclass__()

    class MissingBase:
        pass

    with pytest.raises(TypeError) as error:

        class Broken(
            HookBase,
            metaclass=ExpectedBasesMeta,
            expected_bases=(MissingBase,),
        ):
            descriptor: ClassVar[RecordingDescriptor] = RecordingDescriptor()

        _ = Broken

    assert str(error.value) == "Broken must inherit MissingBase"
    assert events == ["set_name:descriptor", "init_subclass"]


def test_tuple_subclass_requirements_are_snapshotted_once() -> None:
    events: list[str] = []

    class MissingBase:
        pass

    class StatefulRequirements(tuple[object, ...]):
        iteration_count: int = 0

        def __iter__(self) -> Iterator[object]:
            self.iteration_count += 1
            if self.iteration_count == 1:
                return iter((MissingBase,))
            return iter(("not-a-type",))

    class RecordingDescriptor:
        def __set_name__(self, owner: type[object], name: str) -> None:
            events.append(f"set_name:{name}")

    class HookBase:
        def __init_subclass__(cls) -> None:
            events.append("init_subclass")
            super().__init_subclass__()

    requirements: StatefulRequirements = StatefulRequirements((MissingBase,))

    with pytest.raises(TypeError) as error:

        class Broken(
            HookBase,
            metaclass=ExpectedBasesMeta,
            expected_bases=cast(tuple[type, ...], requirements),
        ):
            descriptor: ClassVar[RecordingDescriptor] = RecordingDescriptor()

        _ = Broken

    assert str(error.value) == "Broken must inherit MissingBase"
    assert requirements.iteration_count == 1
    assert events == ["set_name:descriptor", "init_subclass"]


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


def test_prepared_namespace_identity_is_preserved_through_metaclass_mro() -> None:
    class PreparedNamespace(dict[str, object]):
        pass

    class IdentityCheckingMeta(type):
        prepared_namespace: ClassVar[dict[str, object] | None] = None
        received_namespace: ClassVar[Mapping[str, object] | None] = None

        @classmethod
        def __prepare__(
            mcls,
            name: str,
            bases: tuple[type, ...],
            /,
            **kwargs: object,
        ) -> dict[str, object]:
            namespace: PreparedNamespace = PreparedNamespace()
            mcls.prepared_namespace = namespace
            return namespace

        def __new__(
            cls: type["IdentityCheckingMeta"],
            name: str,
            bases: tuple[type, ...],
            namespace: Mapping[str, object],
            **kwargs: object,
        ) -> "IdentityCheckingMeta":
            cls.received_namespace = namespace
            return super().__new__(
                cls,
                name,
                bases,
                dict(namespace),
                **kwargs,
            )

    class CombinedMeta(ExpectedBasesMeta, IdentityCheckingMeta):
        pass

    class Complete(metaclass=CombinedMeta):
        pass

    assert Complete.__name__ == "Complete"
    assert CombinedMeta.received_namespace is CombinedMeta.prepared_namespace


def test_expected_bases_is_consumed_before_cooperative_metaclass_init() -> None:
    events: list[str] = []

    class StrictLifecycleMeta(type):
        def __new__(
            cls: type["StrictLifecycleMeta"],
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, object],
            *,
            marker: str,
        ) -> "StrictLifecycleMeta":
            events.append(f"new:{marker}")
            return super().__new__(cls, name, bases, namespace)

        def __init__(
            self,
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, object],
            *,
            marker: str,
        ) -> None:
            events.append(f"init:{marker}")
            super().__init__(name, bases, namespace)

    class CombinedMeta(ExpectedBasesMeta, StrictLifecycleMeta):
        pass

    class RequiredBase:
        pass

    class Complete(
        RequiredBase,
        metaclass=CombinedMeta,
        expected_bases=(RequiredBase,),
        marker="cooperative",
    ):
        pass

    assert Complete.__name__ == "Complete"
    assert events == ["new:cooperative", "init:cooperative"]


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
