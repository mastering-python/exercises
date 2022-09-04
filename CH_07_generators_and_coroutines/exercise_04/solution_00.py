# Write a generator that uses the sieve of Eratosthenes to generate prime 
# numbers.

import itertools


def generate_primes():
    '''Generate prime numbers using the sieve of Eratosthenes.'''
    primes = []
    for i in itertools.count(2):
        if all(i % prime != 0 for prime in primes):
            primes.append(i)
            yield i


def main():
    primes = generate_primes()
    for _ in range(20):
        print(next(primes))


if __name__ == '__main__':
    main()
