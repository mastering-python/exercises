"""Validate required base classes with a metaclass."""

from collections.abc import Mapping


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
        class_namespace: dict[str, object] = dict(namespace)
        created_class: ExpectedBasesMeta = super().__new__(
            cls,
            name,
            bases,
            class_namespace,
            **kwargs,
        )
        missing_bases: tuple[type, ...] = tuple(
            base for base in expected_bases if not issubclass(created_class, base)
        )
        if missing_bases:
            missing_names: str = ", ".join(base.__name__ for base in missing_bases)
            raise TypeError(f"{name} must inherit {missing_names}")
        return created_class


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
