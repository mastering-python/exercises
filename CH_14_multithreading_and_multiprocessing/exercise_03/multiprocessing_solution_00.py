# Read all files in a directory and sum the size of the files by
# reading each file using `multiprocessing`

import logging
import multiprocessing
import pathlib

# Directory to process
PATH = pathlib.Path(__file__).parent.parent

# We need to setup the logging outside of the
# `if __name__ == '__main__'` block because the
# `multiprocessing` module will not execute that section.
logging.basicConfig(level=logging.INFO)


def get_size(path: pathlib.Path):
    size = path.stat().st_size
    logging.info(
        '%s is %d bytes',
        path.relative_to(PATH),
        size,
    )
    return size


def main(path: pathlib.Path):
    with multiprocessing.Pool() as pool:
        total_size = sum(pool.map(get_size, path.iterdir()))

        print(f'Total size for {path} is: {total_size}')


if __name__ == '__main__':
    main(PATH)
