"""Validate required base classes with a metaclass."""

from collections.abc import Mapping
from typing import cast


def _validate_expected_bases(
    name: str,
    expected_bases: object,
) -> tuple[type, ...]:
    """Validate the required-base contract before class construction."""
    if not isinstance(expected_bases, tuple):
        raise TypeError(f"{name} expected_bases must be a tuple containing only types")
    requirement_source: tuple[object, ...] = cast(
        tuple[object, ...],
        expected_bases,
    )
    requirements: tuple[object, ...] = tuple(iter(requirement_source))
    if not all(isinstance(base, type) for base in requirements):
        raise TypeError(f"{name} expected_bases must be a tuple containing only types")
    return cast(tuple[type, ...], requirements)


class SomeBaseClass:
    """Provide the base required by the example class."""


class ExpectedBasesMeta(type):
    """Require completed classes to inherit selected base classes."""

    def __new__(
        cls: type["ExpectedBasesMeta"],
        name: str,
        bases: tuple[type, ...],
        namespace: Mapping[str, object],
        *,
        expected_bases: tuple[type, ...] = (),
        **kwargs: object,
    ) -> "ExpectedBasesMeta":
        """Create a class and validate its full inheritance hierarchy."""
        requirements: tuple[type, ...] = _validate_expected_bases(
            name,
            expected_bases,
        )
        class_namespace: dict[str, object] = cast(dict[str, object], namespace)
        created_class: ExpectedBasesMeta = super().__new__(
            cls,
            name,
            bases,
            class_namespace,
            **kwargs,
        )
        missing_bases: tuple[type, ...] = tuple(
            base for base in requirements if not issubclass(created_class, base)
        )
        if missing_bases:
            missing_names: str = ", ".join(base.__name__ for base in missing_bases)
            raise TypeError(f"{name} must inherit {missing_names}")
        return created_class

    def __init__(
        self,
        name: str,
        bases: tuple[type, ...],
        namespace: Mapping[str, object],
        *,
        expected_bases: tuple[type, ...] = (),
        **kwargs: object,
    ) -> None:
        """Consume base requirements and cooperatively initialize the class."""
        class_namespace: dict[str, object] = cast(dict[str, object], namespace)
        super().__init__(name, bases, class_namespace, **kwargs)


class Trade(
    SomeBaseClass,
    metaclass=ExpectedBasesMeta,
    expected_bases=(SomeBaseClass,),
):
    """Demonstrate a class satisfying its required-base contract."""


def _inherits_base(candidate: type, expected_base: type) -> bool:
    """Return whether a class satisfies one base requirement."""
    return issubclass(candidate, expected_base)


def main() -> None:
    """Run the valid metaclass demonstration."""
    print(_inherits_base(Trade, SomeBaseClass))


if __name__ == "__main__":
    main()
