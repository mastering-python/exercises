# Read all files in a directory and sum the size of the files by
# reading each file using `threading` or `multiprocessing`
#
# As above, but walk through the directories recursively by
# letting the thread/process queue new items while running.


import logging
import pathlib
import queue
import threading

# Directory to process
PATH = pathlib.Path(__file__).parent.parent
WORKERS = 8
POLL_INTERVAL = 0.25


class FileSizeThread(threading.Thread):
    # Create a `stop` event so we can stop the thread externally
    stop: threading.Event
    size: int
    queue: queue.Queue

    def __init__(self, queue):
        super().__init__()
        self.queue = queue
        self.size = 0
        self.stop = threading.Event()

    def run(self):
        while not self.stop.is_set():
            # Get the next item from the queue if available. If the
            # queue is empty, wait for 0.25 second and try again
            # unless we are told to stop.
            try:
                path = self.queue.get(timeout=POLL_INTERVAL)
            except queue.Empty:
                continue

            # Walk through the directory and sum the filesizes
            # for files and queue up directories
            for child in path.iterdir():
                self.process_path(child)

    def process_path(self, child):
        if child.is_dir():
            self.queue.put(child)
        else:
            size = child.stat().st_size
            self.size += size
            logging.info(
                '%s is %d bytes',
                child.relative_to(PATH),
                size,
            )


def main(path: pathlib.Path):
    threads = []
    q = queue.Queue()
    q.put(path)

    # Create, start and store the worker threads
    for _ in range(WORKERS):
        thread = FileSizeThread(q)
        thread.start()
        threads.append(thread)

    # Stop all threads
    for thread in threads:
        thread.stop.set()

    # Wait for all threads to finish and sum their sizes
    total_size = 0
    for thread in threads:
        thread.join()
        total_size += thread.size

    print(f'Total size for {path} is: {total_size}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(PATH)
