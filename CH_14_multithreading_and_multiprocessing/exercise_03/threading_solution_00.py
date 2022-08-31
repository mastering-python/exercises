# Read all files in a directory and sum the size of the files by
# reading each file using `threading`

import logging
import pathlib
import threading

# Directory to process
PATH = pathlib.Path(__file__).parent.parent


class FileSizeThread(threading.Thread):

    def __init__(self, path: pathlib.Path):
        super().__init__()
        self.path = path
        self.size = 0

    def run(self):
        self.size = self.path.stat().st_size
        logging.info(
            '%s is %d bytes',
            self.path.relative_to(PATH),
            self.size,
        )


def main(path: pathlib.Path):
    threads = []
    for child in path.iterdir():
        thread = FileSizeThread(child)
        thread.start()
        threads.append(thread)

    total_size = 0
    for thread in threads:
        thread.join()
        total_size += thread.size

    print(f'Total size for {path} is: {total_size}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(PATH)
