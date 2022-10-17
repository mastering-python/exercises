import itertools
import functools
import contextlib
import datetime
from solution_00 import generate_primes


@contextlib.contextmanager
def timer():
    s = datetime.datetime.now()
    yield
    e = datetime.datetime.now()
    print((e - s).total_seconds())


# copy from
# https://github.com/mastering-python/code_2/blob/master/CH_03_pythonic_syntax/T_04_simple_is_better_than_complex.rst
def primes_complicate():
    sieve = dict()
    for num in itertools.count(2):
        if num not in sieve:
            yield num
            sieve[num * num] = [num]
        else:
            for p in sieve[num]:
                sieve.setdefault(p + num, []).append(p)
            del sieve[num]


# copy from
# https://github.com/mastering-python/code_2/blob/master/CH_03_pythonic_syntax/T_04_simple_is_better_than_complex.rst
def primes_complex():
    sieve = itertools.count(2)
    while True:
        yield (prime := next(sieve))
        sieve = filter(prime.__rmod__, sieve)


def main():
    print('complicate')
    with timer():
        list(itertools.islice(primes_complicate(), 10000))

    print('complex filter')
    with timer():
        list(itertools.islice(primes_complex(), 10000))

    print('solution_00, complex for')
    with timer():
        list(itertools.islice(generate_primes(), 10000))


if __name__ == '__main__':
    main()
