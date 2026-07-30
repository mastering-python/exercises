"""Module-level doctest example.

>>> MODULE_VALUE + 1
4
"""

MODULE_VALUE: int = 3


def add_module_value(value: int) -> int:
    """Add the module value.

    >>> add_module_value(4)
    7
    """
    return value + MODULE_VALUE


class Multiplier:
    """Multiply configured values.

    >>> Multiplier(3).apply(4)
    12
    """

    def __init__(self, factor: int) -> None:
        self.factor: int = factor

    def apply(self, value: int) -> int:
        """Apply the configured factor.

        >>> Multiplier(5).apply(2)
        10
        """
        return self.factor * value
