"""Validate required class attributes with a metaclass."""

from collections.abc import Mapping
from inspect import getattr_static

_MISSING_ATTRIBUTE: object = object()


class ExpectedAttrsMeta(type):
    """Require attributes to be available on each completed class."""

    def __new__(
        cls: type["ExpectedAttrsMeta"],
        name: str,
        bases: tuple[type, ...],
        namespace: Mapping[str, object],
        *,
        required_attributes: tuple[str, ...] = (),
        **kwargs: object,
    ) -> "ExpectedAttrsMeta":
        """Create a class, then validate its direct and inherited attributes."""
        class_namespace: dict[str, object] = dict(namespace)
        created_class: ExpectedAttrsMeta = super().__new__(
            cls,
            name,
            bases,
            class_namespace,
            **kwargs,
        )
        missing: tuple[str, ...] = tuple(
            attribute
            for attribute in required_attributes
            if getattr_static(created_class, attribute, _MISSING_ATTRIBUTE)
            is _MISSING_ATTRIBUTE
        )
        if missing:
            missing_text: str = ", ".join(missing)
            raise AttributeError(
                f"{name} missing required attribute(s): {missing_text}"
            )
        return created_class


class Trade(
    metaclass=ExpectedAttrsMeta,
    required_attributes=("buy", "sell"),
):
    """Demonstrate a class satisfying a required-attribute contract."""

    def buy(self) -> str:
        """Return the demonstrated buy operation."""
        return "buy"

    def sell(self) -> str:
        """Return the demonstrated sell operation."""
        return "sell"


def main() -> None:
    """Run the valid metaclass demonstration."""
    trade: Trade = Trade()
    print(trade.buy(), trade.sell())


if __name__ == "__main__":
    main()
