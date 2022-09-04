# Create a metaclass to test if specific classes are inherited.


class SomeBaseClass:
    pass


class ExpectedBasesMeta(type):
    _expected_bases = [SomeBaseClass]

    def __new__(cls, name, bases, attrs):
        for base in cls._expected_bases:
            if base not in bases:
                raise TypeError(
                    f'{name} is not inheriting {base}'
                )
        return super().__new__(cls, name, bases, attrs)


class Trade(SomeBaseClass, metaclass=ExpectedBasesMeta):
    pass


class BrokenTrade(metaclass=ExpectedBasesMeta):
    pass
