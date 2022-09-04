# Modify the memoization function to have a cache per function instead of a 
# global one.

import functools


def memoize(function):
    # Store the cache as attribute of the function so we can
    # apply the decorator to multiple functions without
    # sharing the cache.
    function.cache = dict()

    def safe_hash(args):
        '''
        In the case of unhashable types use the `repr()` to be hashable.
        '''
        try:
            return hash(args)
        except TypeError:
            return repr(args)

    @functools.wraps(function)
    def _memoize(*args):
        # If the cache is not available, call the function
        # Note that all args need to be hashable
        key = safe_hash(args)
        if key not in function.cache:
            function.cache[key] = function(*args)
        return function.cache[key]

    return _memoize


@memoize
def printer(*args):
    print(args)


def main():
    # Should work as expected
    printer('a', 'b', 'c')

    # Would have issues with the original memoize function because the
    # parameters are unhashable
    printer(dict(a=1, b=2, c=3))


if __name__ == '__main__':
    main()
