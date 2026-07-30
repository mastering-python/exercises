"""Generate prime numbers with an incremental Eratosthenes sieve."""

from collections.abc import Iterator
from itertools import islice


def generate_primes() -> Iterator[int]:
    """Yield every prime in ascending order forever."""
    composites: dict[int, list[int]] = {}
    candidate: int = 2
    while True:
        factors: list[int] | None = composites.pop(candidate, None)
        if factors is None:
            yield candidate
            composites[candidate * candidate] = [candidate]
        else:
            prime: int
            for prime in factors:
                composites.setdefault(candidate + prime, []).append(prime)
        candidate += 1


def main() -> None:
    """Print a bounded prefix of the infinite prime sequence."""
    primes: list[int] = list(islice(generate_primes(), 20))
    print(primes)


if __name__ == "__main__":
    main()
