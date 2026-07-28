"""Tests for numeric constraints and runtime parameter type checking."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from typing import cast

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
    [(1, 1), (2, 1), (float("nan"), 1)],
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
