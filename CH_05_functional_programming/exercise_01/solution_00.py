# Implement the quicksort algorithm.
import random

# one-liner approach
qs = lambda xs: xs if len(xs) <= 1 else qs(
    [x for x in xs[1:] if x < xs[0]]) + [xs[0]] + qs(
    [x for x in xs[1:] if x >= xs[0]])


# more verbose approach
def quicksort(xs):
    if len(xs) <= 1:
        return xs
    else:
        left = quicksort([x for x in xs[1:] if x < xs[0]])
        right = quicksort([x for x in xs[1:] if x >= xs[0]])
        middle = [xs[0]]
        return left + middle + right


def main():
    # test
    xs = random.sample(range(1000), 100)
    assert quicksort(xs) == sorted(xs)
    assert qs(xs) == sorted(xs)


if __name__ == '__main__':
    main()
