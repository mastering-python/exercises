Chapter 8 - metaclasses
=======================================================================================================================

1. Create a metaclass to test if attributes/methods are available.
2. Create a metaclass to test if specific classes are inherited.
3. Build a metaclass that wraps every method with a decorator (could be useful for logging/de- bugging purposes), something with a signature like this:

    class SomeClass(metaclass=WrappingMeta, wrapper=some_wrapper):
