# Enhance the `type_check` decorator to include additional checks such as 
# requiring a number to be greater than or less than a given value.
import abc
import functools
import inspect

import pytest


# Note: the exercise erroneously mentions `type_check` instead of
# `enforce_type_hints`. For clarity the function was renamed in the text of
# the book, but it seems I forgot about the exercise.


class Constraint(abc.ABC):
    def __call__(self, name, value):
        return False

    def to_string(self, name, value, constraint):
        return f'{name}={value!r} must be {constraint}'

    def __str__(self):
        return self.to_string()


class Gt(Constraint):
    def __init__(self, value):
        self.value = value

    def __call__(self, name, value):
        if not value > self.value:
            raise ValueError(self.to_string(name, value))

    def to_string(self, name='x', value='x', constraint='x > y'):
        return super().to_string(name, value, f'greater than {self.value}')


class Between(Constraint):
    def __init__(self, min_value, max_value):
        self.min_value = min_value
        self.max_value = max_value

    def __call__(self, name, value):
        if not self.min_value < value < self.max_value:
            raise ValueError(self.to_string(name, value))

    def to_string(self, name='x', value='x', constraint='x < y < z'):
        return super().to_string(
            name,
            value,
            f'between {self.min_value} and {self.max_value}',
        )


def enforce_type_hints(**constraint_kwargs):
    def _enforce_type_hints(function):
        # Construct the signature from the function which contains
        # the type annotations
        signature = inspect.signature(function)

        @functools.wraps(function)
        def __enforce_type_hints(*args, **kwargs):
            # Bind the arguments and apply the default values
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()

            for key, value in bound.arguments.items():
                param = signature.parameters[key]
                # The annotation should be a callable
                # type/function so we can cast as validation
                if param.annotation:
                    try:
                        bound.arguments[key] = param.annotation(value)
                    except ValueError:
                        raise ValueError(
                            f'{key} must be {param.annotation.__name__}'
                        )

                if key in constraint_kwargs:
                    constraint_kwargs[key](key, value)

            return function(*bound.args, **bound.kwargs)

        return __enforce_type_hints

    return _enforce_type_hints


@enforce_type_hints(bacon=Gt(0), eggs=Between(1, 4))
def sandwich(bacon: float, eggs: int):
    print(f'bacon: {bacon!r}, eggs: {eggs!r}')


def test_sandwich():
    sandwich(1, 2)
    sandwich(5, 3)

    try:
        sandwich(1, 0)
    except ValueError as e:
        assert str(e) == 'eggs=0 must be between 1 and 4'
    else:
        assert False

    try:
        sandwich(1, 5)
    except ValueError as e:
        assert str(e) == 'eggs=5 must be between 1 and 4'
    else:
        assert False

    try:
        sandwich(0, 5)
    except ValueError as e:
        assert str(e) == 'bacon=0 must be greater than 0'
    else:
        assert False

if __name__ == '__main__':
    pytest.main(['-vv'])
