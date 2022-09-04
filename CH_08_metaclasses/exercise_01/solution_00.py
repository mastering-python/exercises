# Create a metaclass to test if attributes/methods are available.

class ExpectedAttrsMeta(type):
    _expected_attrs = ['buy', 'sell']

    def __new__(cls, name, bases, attrs):
        for attr in cls._expected_attrs:
            if attr not in attrs:
                raise AttributeError(
                    f'{attr} attribute is missing from {name} class'
                )
        return super().__new__(cls, name, bases, attrs)


class Trade(metaclass=ExpectedAttrsMeta):
    pass
