"""Tests for numeric constraints and runtime parameter type checking."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from fractions import Fraction
from typing import Literal, cast

import pytest

from .solution_00 import (
    Between,
    Constraint,
    GreaterThan,
    Gt,
    LessThan,
    enforce_type_hints,
    type_check,
)


def test_greater_than_accepts_value_above_bound() -> None:
    GreaterThan(3).validate("count", 4)


def test_greater_than_rejects_value_at_bound() -> None:
    with pytest.raises(
        ValueError,
        match=r"^count=3 must be greater than 3$",
    ):
        GreaterThan(3).validate("count", 3)


def test_less_than_accepts_value_below_bound() -> None:
    LessThan(3).validate("count", 2)


def test_less_than_rejects_value_at_bound() -> None:
    with pytest.raises(
        ValueError,
        match=r"^count=3 must be less than 3$",
    ):
        LessThan(3).validate("count", 3)


@pytest.mark.parametrize("value", [1, 4])
def test_between_is_exclusive_by_default(value: int) -> None:
    with pytest.raises(
        ValueError,
        match=rf"^count={value} must be between 1 and 4 \(exclusive\)$",
    ):
        Between(1, 4).validate("count", value)


def test_between_accepts_value_strictly_inside_bounds() -> None:
    Between(1, 4).validate("count", 2)


@pytest.mark.parametrize("value", [1, 4])
def test_between_inclusive_accepts_boundary_values(value: int) -> None:
    Between(1, 4, inclusive=True).validate("count", value)


@pytest.mark.parametrize("value", [0, 5])
def test_between_inclusive_rejects_values_outside_bounds(value: int) -> None:
    with pytest.raises(
        ValueError,
        match=rf"^count={value} must be between 1 and 4 \(inclusive\)$",
    ):
        Between(1, 4, inclusive=True).validate("count", value)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: GreaterThan("zero"),
        lambda: LessThan(object()),
        lambda: Between("zero", 1),
        lambda: Between(0, object()),
    ],
)
def test_constraint_bounds_must_be_real(
    factory: Callable[[], object],
) -> None:
    with pytest.raises(TypeError, match=r"^constraint bounds must be real numbers$"):
        factory()


@pytest.mark.parametrize(
    ("lower", "upper"),
    [(1, 1), (2, 1)],
)
def test_between_lower_bound_must_be_less_than_upper_bound(
    lower: float,
    upper: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"^lower bound must be less than upper bound$",
    ):
        Between(lower, upper)


def test_between_inclusive_option_must_be_boolean() -> None:
    with pytest.raises(TypeError, match=r"^inclusive must be a bool$"):
        Between(1, 4, inclusive=cast(bool, 1))


@pytest.mark.parametrize(
    "constraint",
    [GreaterThan(0), LessThan(10), Between(0, 10)],
)
def test_constraints_reject_nonnumeric_values(
    constraint: Constraint,
) -> None:
    with pytest.raises(
        TypeError,
        match=r"^count='5' must be a real number$",
    ):
        constraint.validate("count", "5")


@pytest.mark.parametrize(
    "constraint",
    [GreaterThan(0), LessThan(10), Between(0, 10)],
    ids=["greater-than", "less-than", "between"],
)
def test_constraints_reject_boolean_values(
    constraint: Constraint,
) -> None:
    with pytest.raises(
        TypeError,
        match=r"^count=True must be a real number$",
    ):
        constraint.validate("count", True)


@pytest.mark.parametrize(
    "factory",
    [
        lambda: GreaterThan(True),
        lambda: LessThan(False),
        lambda: Between(False, 1),
        lambda: Between(0, True),
    ],
)
def test_constraint_bounds_reject_booleans(
    factory: Callable[[], object],
) -> None:
    with pytest.raises(TypeError, match=r"^constraint bounds must be real numbers$"):
        factory()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: GreaterThan(float("nan")),
        lambda: GreaterThan(float("inf")),
        lambda: GreaterThan(float("-inf")),
        lambda: LessThan(float("nan")),
        lambda: LessThan(float("inf")),
        lambda: LessThan(float("-inf")),
        lambda: Between(float("nan"), 1),
        lambda: Between(float("inf"), 1),
        lambda: Between(float("-inf"), 1),
        lambda: Between(0, float("nan")),
        lambda: Between(0, float("inf")),
        lambda: Between(0, float("-inf")),
    ],
)
def test_constraint_bounds_must_be_finite(
    factory: Callable[[], object],
) -> None:
    with pytest.raises(
        ValueError,
        match=r"^constraint bounds must be finite real numbers$",
    ):
        factory()


@pytest.mark.parametrize(
    ("constraint", "value"),
    [
        (GreaterThan(0), float("nan")),
        (GreaterThan(0), float("inf")),
        (GreaterThan(0), float("-inf")),
        (LessThan(0), float("nan")),
        (LessThan(0), float("inf")),
        (LessThan(0), float("-inf")),
        (Between(-1, 1), float("nan")),
        (Between(-1, 1), float("inf")),
        (Between(-1, 1), float("-inf")),
    ],
    ids=[
        "greater-than-nan",
        "greater-than-infinity",
        "greater-than-negative-infinity",
        "less-than-nan",
        "less-than-infinity",
        "less-than-negative-infinity",
        "between-nan",
        "between-infinity",
        "between-negative-infinity",
    ],
)
def test_constraints_reject_nonfinite_values_before_comparison(
    constraint: Constraint,
    value: float,
) -> None:
    with pytest.raises(
        ValueError,
        match=r"^count=.* must be a finite real number$",
    ):
        constraint.validate("count", value)


def test_constraints_preserve_huge_finite_integers() -> None:
    huge: int = 10**10_000

    GreaterThan(huge - 1).validate("count", huge)
    LessThan(huge + 1).validate("count", huge)
    Between(huge - 1, huge + 1).validate("count", huge)


def test_constraints_support_finite_fractions() -> None:
    value: Fraction = Fraction(1, 2)

    GreaterThan(Fraction(1, 3)).validate("ratio", value)
    LessThan(Fraction(2, 3)).validate("ratio", value)
    Between(Fraction(1, 3), Fraction(2, 3)).validate("ratio", value)


def test_constraint_implementations_are_frozen() -> None:
    constraint: GreaterThan = GreaterThan(0)
    attribute: str = "value"

    with pytest.raises(FrozenInstanceError):
        setattr(constraint, attribute, 1)


def test_decorator_accepts_valid_positional_and_keyword_arguments() -> None:
    @type_check(
        bacon=GreaterThan(0),
        eggs=Between(1, 4),
        temperature=LessThan(100),
    )
    def sandwich(bacon: float, eggs: int, *, temperature: float) -> str:
        return f"{bacon}:{eggs}:{temperature}"

    assert sandwich(1.5, 2, temperature=90.0) == "1.5:2:90.0"
    assert sandwich(bacon=3.0, eggs=3, temperature=50.0) == "3.0:3:50.0"


def test_parameter_types_are_checked_before_constraints() -> None:
    calls: list[tuple[str, object]] = []

    class RecordingConstraint:
        def validate(self, name: str, value: object) -> None:
            calls.append((name, value))

    @type_check(value=RecordingConstraint())
    def identify(value: int) -> int:
        return value

    with pytest.raises(
        TypeError,
        match=r"^value expected int, got str$",
    ):
        identify("3")  # type: ignore[arg-type]

    assert calls == []


def test_annotated_parameters_without_constraints_are_checked() -> None:
    @type_check()
    def repeat(text: str, count: int) -> str:
        return text * count

    with pytest.raises(
        TypeError,
        match=r"^text expected str, got int$",
    ):
        repeat(3, 2)  # type: ignore[arg-type]


def test_unannotated_constrained_parameter_rejects_nonnumeric_value() -> None:
    @type_check(value=GreaterThan(0))
    def identity(value) -> object:  # type: ignore[no-untyped-def]
        return cast(object, value)

    with pytest.raises(
        TypeError,
        match=r"^value='3' must be a real number$",
    ):
        identity("3")


def test_default_arguments_are_bound_checked_and_constrained() -> None:
    @type_check(count=GreaterThan(0))
    def repeat(text: str, count: int = 2) -> str:
        return text * count

    assert repeat("go") == "gogo"


def test_invalid_default_is_checked_when_omitted() -> None:
    @type_check(count=GreaterThan(0))
    def repeat(text: str, count: int = 0) -> str:
        return text * count

    with pytest.raises(
        ValueError,
        match=r"^count=0 must be greater than 0$",
    ):
        repeat("go")


def test_unknown_constraint_name_is_rejected_at_decoration() -> None:
    decorator = type_check(missing=GreaterThan(0))

    with pytest.raises(
        TypeError,
        match=r"^unknown constrained parameter: 'missing'$",
    ):

        @decorator
        def identity(value: int) -> int:
            return value

        assert callable(identity)


def test_constraint_must_provide_validate_method() -> None:
    decorator = type_check(value=cast(Constraint, object()))

    with pytest.raises(
        TypeError,
        match=r"^constraint for 'value' must provide validate\(name, value\)$",
    ):

        @decorator
        def identity(value: int) -> int:
            return value

        assert callable(identity)


def test_type_check_does_not_coerce_values() -> None:
    calls: list[int] = []

    @type_check(value=GreaterThan(0))
    def record(value: int) -> int:
        calls.append(value)
        return value

    with pytest.raises(TypeError, match=r"^value expected int, got str$"):
        record("3")  # type: ignore[arg-type]

    assert calls == []


def test_return_annotation_is_not_validated() -> None:
    @type_check()
    def unchecked_return() -> int:
        return cast(int, "not checked")

    result: object = unchecked_return()

    assert result == "not checked"


def test_unresolved_return_annotation_is_not_resolved() -> None:
    @type_check()
    def identity(value: int) -> object:
        return value

    original = inspect.unwrap(identity)
    original.__annotations__["return"] = "MissingReturnValue"

    assert identity(1) == 1


def test_literal_integer_rejects_equal_boolean() -> None:
    @type_check()
    def identify(value: Literal[1]) -> Literal[1]:
        return value

    with pytest.raises(
        TypeError,
        match=r"^value expected Literal\[1\], got bool$",
    ):
        identify(True)  # type: ignore[arg-type]


def test_literal_boolean_rejects_equal_integer() -> None:
    @type_check()
    def identify(value: Literal[True]) -> Literal[True]:
        return value

    with pytest.raises(
        TypeError,
        match=r"^value expected Literal\[True\], got int$",
    ):
        identify(1)  # type: ignore[arg-type]


def test_function_local_forward_reference_resolves_on_first_call() -> None:
    class LocalValue:
        pass

    @type_check()
    def identify(value: LocalValue) -> object:
        return value

    value: LocalValue = LocalValue()

    assert identify(value) is value


def test_free_function_forward_reference_cannot_be_spoofed_by_argument() -> None:
    class ExpectedValue:
        pass

    @type_check()
    def identify(value: ExpectedValue) -> object:
        return value

    SpoofValue: type[object] = type("ExpectedValue", (), {})

    with pytest.raises(
        TypeError,
        match=r"^value expected ExpectedValue, got ExpectedValue$",
    ):
        identify(SpoofValue())  # type: ignore[arg-type]


def test_class_self_forward_reference_resolves_after_class_creation() -> None:
    class Node:
        @type_check()
        def connect(self, other: Node) -> Node:
            return other

    first: Node = Node()
    second: Node = Node()

    assert first.connect(second) is second


def test_class_self_forward_reference_cannot_be_spoofed_by_argument() -> None:
    class Node:
        @type_check()
        def connect(self, other: Node) -> object:
            return other

    SpoofNode: type[object] = type("Node", (), {})

    with pytest.raises(
        TypeError,
        match=r"^other expected Node, got Node$",
    ):
        Node().connect(SpoofNode())  # type: ignore[arg-type]


def test_classmethod_self_reference_uses_verified_declared_owner() -> None:
    class Node:
        @classmethod
        @type_check()
        def connect(cls, other: Node) -> object:
            return other

    node: Node = Node()
    SpoofNode: type[object] = type("Node", (), {})

    with pytest.raises(
        TypeError,
        match=r"^other expected Node, got Node$",
    ):
        Node.connect(SpoofNode())  # type: ignore[arg-type]

    assert Node.connect(node) is node


def test_forged_receiver_cannot_claim_declared_owner_identity() -> None:
    class Node:
        @type_check()
        def connect(self, other: Node) -> object:
            return other

    ForgedNode: type[object] = type(
        "Node",
        (),
        {"__module__": Node.__module__},
    )
    ForgedNode.__qualname__ = Node.__qualname__
    forged: object = ForgedNode()

    with pytest.raises(NameError, match=r"name 'Node' is not defined"):
        Node.connect(forged, forged)  # type: ignore[arg-type]


def test_module_forward_reference_resolves_after_definition() -> None:
    namespace: dict[str, object] = {"type_check": type_check}
    exec(
        "from __future__ import annotations\n"
        "@type_check()\n"
        "def identify(value: LaterValue) -> object:\n"
        "    return value\n"
        "class LaterValue:\n"
        "    pass\n",
        namespace,
    )
    identify = cast(Callable[[object], object], namespace["identify"])
    later_value = cast(type[object], namespace["LaterValue"])()

    assert identify(later_value) is later_value


def test_unresolved_forward_reference_raises_only_when_called() -> None:
    @type_check()
    def identify(value: object) -> object:
        return value

    original = inspect.unwrap(identify)
    original.__annotations__["value"] = "MissingValue"

    assert callable(identify)

    with pytest.raises(NameError, match=r"name 'MissingValue' is not defined"):
        identify(object())


def test_resolved_type_hints_are_cached_after_success() -> None:
    @type_check()
    def identify(value: int) -> object:
        return value

    assert identify(1) == 1

    original = inspect.unwrap(identify)
    original.__annotations__["value"] = "MissingAfterResolution"

    assert identify(2) == 2


def test_function_metadata_and_signature_are_preserved() -> None:
    def original(value: int, *, scale: float = 1.0) -> float:
        """Scale a value."""
        return value * scale

    decorated = type_check(value=GreaterThan(0))(original)

    assert decorated.__name__ == original.__name__
    assert decorated.__qualname__ == original.__qualname__
    assert decorated.__module__ == original.__module__
    assert decorated.__doc__ == original.__doc__
    assert decorated.__annotations__ == original.__annotations__
    assert inspect.unwrap(decorated) is original
    assert inspect.signature(decorated) == inspect.signature(original)


def test_signature_binding_errors_propagate() -> None:
    @type_check()
    def add(left: int, right: int) -> int:
        return left + right

    with pytest.raises(TypeError, match=r"missing a required argument: 'right'"):
        add(1)  # type: ignore[call-arg]

    with pytest.raises(TypeError, match=r"multiple values for argument 'left'"):
        add(1, left=2, right=3)  # type: ignore[misc]

    with pytest.raises(TypeError, match=r"unexpected keyword argument 'extra'"):
        add(left=1, right=2, extra=3)  # type: ignore[call-arg]


def test_constraint_cannot_target_variadic_positional_parameter() -> None:
    decorator = type_check(values=GreaterThan(0))

    with pytest.raises(
        TypeError,
        match=r"^constraint for variadic parameter 'values' is not supported$",
    ):

        @decorator
        def collect(*values: object) -> tuple[object, ...]:
            return values

        assert callable(collect)


def test_constraint_cannot_target_variadic_keyword_parameter() -> None:
    decorator = type_check(options=GreaterThan(0))

    with pytest.raises(
        TypeError,
        match=r"^constraint for variadic parameter 'options' is not supported$",
    ):

        @decorator
        def collect(**options: object) -> dict[str, object]:
            return options

        assert callable(collect)


def test_unconstrained_variadic_annotations_are_checked_elementwise() -> None:
    @type_check()
    def collect(*values: int, **options: int) -> tuple[tuple[int, ...], dict[str, int]]:
        return values, options

    assert collect(1, 2, enabled=3) == ((1, 2), {"enabled": 3})

    with pytest.raises(TypeError, match=r"^values expected int, got str$"):
        collect(1, "2")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match=r"^options expected int, got str$"):
        collect(enabled="3")  # type: ignore[arg-type]


def test_wrapped_function_errors_propagate() -> None:
    @type_check()
    def explode(value: int) -> int:
        raise RuntimeError(f"boom: {value}")

    with pytest.raises(RuntimeError, match=r"^boom: 1$"):
        explode(1)


def test_decorators_keep_independent_constraint_configuration() -> None:
    @type_check(value=GreaterThan(0))
    def positive(value: int) -> int:
        return value

    @type_check(value=LessThan(0))
    def negative(value: int) -> int:
        return value

    assert positive(1) == 1
    assert negative(-1) == -1

    with pytest.raises(ValueError, match=r"must be greater than 0$"):
        positive(-1)

    with pytest.raises(ValueError, match=r"must be less than 0$"):
        negative(1)


def test_aliases_preserve_identity_and_behavior() -> None:
    assert Gt is GreaterThan
    assert enforce_type_hints is type_check

    @enforce_type_hints(value=Gt(0))
    def identity(value: int) -> int:
        return value

    assert identity(1) == 1

    with pytest.raises(ValueError, match=r"^value=0 must be greater than 0$"):
        identity(0)
