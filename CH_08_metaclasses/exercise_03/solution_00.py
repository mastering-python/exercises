# Build a metaclass that wraps every method with a decorator (could be 
# useful for logging/de- bugging purposes), something with a signature like 
# this:
#
# class SomeClass(metaclass=WrappingMeta, wrapper=some_wrapper):

class WrappingMeta(type):
    def __new__(cls, name, bases, attrs, wrapper):
        for attr_name, attr_value in attrs.items():
            if callable(attr_value):
                attrs[attr_name] = wrapper(attr_value)
        return super().__new__(cls, name, bases, attrs)


def print_call(func):
    def wrapped(*args, **kwargs):
        print(f'Calling {func.__name__}({args}, {kwargs})')
        return func(*args, **kwargs)

    return wrapped


class SomeClass(metaclass=WrappingMeta, wrapper=print_call):
    def some_method(self):
        print('some_method() called')


if __name__ == '__main__':
    SomeClass().some_method()
