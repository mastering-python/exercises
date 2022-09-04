# Modify the memoization function to function with unhashable types.

import functools


cache = dict()

def memoize(function):
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
        # key = function, safe_hash(args)
        key = function, args
        if key not in cache:
            cache[key] = function(*args)
        return cache[key]

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
