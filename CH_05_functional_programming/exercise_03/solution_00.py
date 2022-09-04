# Write a groupby function that returns lists of results instead of 
# generators.

import pprint


def groupby(iterable, key=None):
    '''
    Return a dictionary of lists of items grouped by the key function.

    Note that as opposed to the itertools.groupby function, this function
    does not require the iterable to be sorted.
    '''
    if key is None:
        key = lambda x: x
    groups = {}
    for item in iterable:
        groups.setdefault(key(item), []).append(item)
    return groups


def main():
    # Demo data from the itertools docs
    pprint.pprint(groupby('AAAABBBCCDAABBB'))
    pprint.pprint(groupby('AAAABBBCCD'))


if __name__ == '__main__':
    main()
