# Create a version of `functools.cached_property` that can be recalculated 
# as needed.
from datetime import datetime


class _NotFound:
    pass


class CachedProperty:
    # Note that this is a very basic version of `functools.cached_property`. If
    # you wish to use this in production I suggest looking at the original
    # `cached_property` decorator and implement the locking and conflict
    # handling as well.

    def __init__(self, func):
        self.func = func

    def clear(self):
        self.cache.pop(self.attrname, None)

    def __set_name__(self, owner, name):
        if not hasattr(owner, '_cache'):
            owner._cache = dict()
            # Add a clear method to the owner class
            setattr(owner, f'clear_{name}', self.clear)

        self.cache = owner._cache
        self.attrname = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        key = self.attrname
        if key not in self.cache:
            self.cache[key] = self.func(instance)

        return self.cache[key]


class SomeClass:

    @CachedProperty
    def current_time(self):
        return datetime.now()


def main():
    some_class = SomeClass()
    a = some_class.current_time
    b = some_class.current_time
    assert a == b
    # Clear the cache. Even though your editor might complain, this method
    # exists. Can you think of a better API to make the cache clearable?
    some_class.clear_current_time()
    c = some_class.current_time
    assert a != c


if __name__ == '__main__':
    main()
