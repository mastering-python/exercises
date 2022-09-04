# Write a groupby function that isn’t affected by sorting.
import collections


def groupby(func, seq):
    groups = collections.defaultdict(list)
    for item in seq:
        groups[func(item)].append(item)
    return groups


def main():
    # Explicitly defined test data for clarity.
    xs = [0, 1, 2, 3, 4, 5, 6, 7]

    assert groupby(lambda x: x % 2, xs) == {
        0: [0, 2, 4, 6],
        1: [1, 3, 5, 7],
    }

    assert groupby(
        lambda x: 'even' if x % 2 == 0 else 'odd',
        xs,
    ) == {'even': [0, 2, 4, 6], 'odd': [1, 3, 5, 7]}

    assert groupby(lambda x: x > 5, xs) == {
        False: [0, 1, 2, 3, 4, 5],
        True: [6, 7],
    }


if __name__ == '__main__':
    main()
