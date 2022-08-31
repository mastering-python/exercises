# Read all files in a directory and sum the size of the files by reading each file using `processing` or `multiprocessing`

import logging
import multiprocessing
import pathlib

# Directory to process
PATH = pathlib.Path(__file__).parent.parent
WORKERS = 8
POLL_INTERVAL = 0.25

# We need to setup the logging outside of the
# `if __name__ == '__main__'` block because the
# `multiprocessing` module will not execute that section.
logging.basicConfig(level=logging.INFO)


class FileSizeProcess(multiprocessing.Process):
    size: multiprocessing.Value
    queue: multiprocessing.Queue

    def __init__(self, size, queue):
        super().__init__()
        self.queue = queue
        self.size = size

    def run(self):
        while True:
            path = self.queue.get()

            total_size = 0
            # Walk through the directory and sum the filesizes
            # for files and queue up directories
            child: pathlib.Path
            for child in path.iterdir():
                if child.is_dir():
                    self.queue.put(child)
                else:
                    size = child.stat().st_size
                    total_size += size
                    logging.info(
                        '%s is %d bytes',
                        child.relative_to(PATH),
                        size,
                    )

            # Update the size in the shared memory. Since this is a
            # relatively slow operation we do it once per loop
            self.size.value += total_size

            # The JoinableQueue requires us to tell it that we are
            # done with the item
            self.queue.task_done()


def main(path: pathlib.Path):
    processs = []
    q = multiprocessing.JoinableQueue()
    q.put(path)

    total_size = multiprocessing.Value('i', 0)

    # Create, start and store the worker processs
    for _ in range(WORKERS):
        process = FileSizeProcess(total_size, q)
        process.start()
        processs.append(process)

    # Wait until all the items in the queue have been processed
    q.join()
    q.close()

    # Terminate all the processs
    for process in processs:
        process.terminate()
        process.join()

    # Wait for all processs to finish and sum their sizes
    print(f'Total size for {path} is: {total_size.value}')


if __name__ == '__main__':
    main(PATH)
