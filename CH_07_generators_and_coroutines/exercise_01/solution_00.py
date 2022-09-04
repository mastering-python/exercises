# Create a generator similar to `itertools.islice()` that allows for a 
# negative step so you can execute `some_list[20:10:-1]`.
import itertools


def islice(iterable, start, stop, step):
    if step > 0:
        assert start <= stop, 'start must be less than stop'
        yield from itertools.islice(iterable, start, stop, step)
    else:
        assert start >= stop, 'start must be greater than stop for negative step'

        output = []
        for i, item in enumerate(iterable):
            if i >= stop:
                output.append(item)
            if i >= start:
                break

        yield from reversed(output)


def main():
    some_iterable = iter(range(100))
    print(list(islice(some_iterable, 20, 10, -1)))

    print(list(islice(some_iterable, 10, 20, 1)))


if __name__ == '__main__':
    main()
