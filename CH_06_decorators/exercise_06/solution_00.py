# Create a single-dispatch decorator that considers all or a configurable
# number of arguments instead of only the first one.
import functools
import inspect
import typing


def fancysingledispatch(*disabled_args, **disabled_kwargs):
    '''
    A single-dispatch decorator that considers all or a configurable
    number of arguments instead of only the first one.

    Args:
        disabled_args: A list of argument names to ignore.
        disabled_kwargs: A list of keyword argument names to ignore.

    '''
    registry = dict()
    disabled_args = set(disabled_args)
    for key, value in disabled_kwargs.items():
        if value:
            disabled_args.add(key)

    def register(function):
        key_parts = []
        for key, type_ in typing.get_type_hints(function).items():
            if key == 'return':
                # Ignore the return type
                continue

            if key in disabled_args:
                key_parts.append(None)
            else:
                key_parts.append(type_)

        registry[tuple(key_parts)] = function
        return function

    def dispatch(function):
        signature = inspect.signature(function)

        @functools.wraps(function)
        def _dispatch(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()

            key_parts = []
            for key, value in bound.arguments.items():
                if key in disabled_args:
                    key_parts.append(None)
                else:
                    key_parts.append(type(value))

            key = tuple(key_parts)
            if key in registry:
                return registry[key](*args, **kwargs)
            else:
                raise TypeError(f'No matching function for {key}')

        _dispatch.register = register
        register(function)
        return _dispatch

    return dispatch


@fancysingledispatch(last_name=True)
def hello(first_name: str, last_name: str, age: None = None) -> str:
    return f'Hello {first_name} {last_name}'


# Since this function only differs in the last_name argument, it will
# override the previous one. The original `hello` function will never get
# called again.
@hello.register
def first_name_only(
    first_name: str,
    last_name: None = None,
    age: None = None,
) -> str:
    return f'Hello {first_name}'


@hello.register
def name_age(first_name: str, last_name: str, age: int) -> str:
    # Reuse the function above
    return hello(first_name, last_name) + f', you are {age} years old'


@hello.register
def name_age_days(first_name: str, last_name: str, age: float) -> str:
    days = int((age % 1) * 365)
    age = int(age)
    return hello(
        first_name,
        last_name
    ) + f', you are {age} years and {days} days old'


def main():
    print(hello('Rick', 'van Hattem'))
    print(hello('Rick', 'van Hattem', age=30))
    print(hello('Rick', 'van Hattem', age=30.5))


if __name__ == '__main__':
    main()
