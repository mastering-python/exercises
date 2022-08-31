# Read all files in a directory and sum the size of the files by
# reading each file using `concurrent.futures`. If you want an
# extra challenge, walk through the directories recursively by
# letting the thread/process queue new items while running.

import concurrent.futures
import logging
import pathlib
import time

# Our current directory
PATH = pathlib.Path(__file__).parent


def get_size(path: pathlib.Path) -> int:
    size = path.stat().st_size
    logging.info('%s is %d bytes', path, size)
    return size


def get_total_size(path) -> int:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        return sum(executor.map(get_size, path.iterdir()))


def get_size_or_queue(
        executor: concurrent.futures.Executor,
        futures: list[concurrent.futures.Future],
        path: pathlib.Path,
) -> int:
    # If the path is a directory, queue up the children
    if path.is_dir():
        for child in path.iterdir():
            futures.append(executor.submit(
                get_size_or_queue, executor, futures, child))

        # A directory has size 0 but we recurse into it
        return 0
    else:
        return get_size(path)


def get_total_size_recursive(path) -> int:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []

        # Note that we are using a regular list as a queue. This is
        # thread-safe because `list.append()` is atomic.
        futures.append(executor.submit(
            get_size_or_queue, executor, futures, path))

        total_size = 0
        for future in futures:
            total_size += future.result()

        return total_size


def main(path: pathlib.Path):
    total_size = get_total_size(path)
    print(f'Total size for {path} is: {total_size}')

    # Sleep so editors such as Pycharm don't mix the output
    time.sleep(0.5)

    total_size = get_total_size_recursive(path)
    print(f'Recursive total size for {path} is: {total_size}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Use the parent directory to get a reasonable list of files
    main(PATH.parent)
