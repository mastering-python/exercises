# Create a class that wraps a generator so it becomes sliceable by using 
# `itertools.islice()` internally.
import itertools


class SliceableGenerator:
    def __init__(self, gen):
        self.gen = gen

    def __getitem__(self, index):
        return list(itertools.islice(self.gen, index.start, index.stop))


def main():
    generator = SliceableGenerator(itertools.count())
    print(generator[10:20])


if __name__ == '__main__':
    main()

