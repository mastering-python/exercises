# Create an `asyncio` wrapper class for a synchronous process
# such as file or network operations using executors

# This example shows an `AsyncioFile` class that makes your file
# operations asynchronous by running them in a separate thread.
# If your operation has a tendency to block the Python GIL you
# could also opt for using a ProcessPoolExecutor instead.
#
# Note that for real-life usage I would recommend the aiofiles
# module over this class.

import asyncio
import concurrent.futures
import functools
import pathlib
from asyncio import AbstractEventLoop
from concurrent.futures import ThreadPoolExecutor


class AsyncExecutorBase:
    _executor: ThreadPoolExecutor
    _loop: AbstractEventLoop

    def __init__(self):
        self._executor = concurrent.futures.ThreadPoolExecutor()
        self._loop = asyncio.get_running_loop()
        super().__init__()

    def _run_in_executor(self, func, *args, **kwargs):
        # Note that this method is not async but can be awaited
        # because it returns a coroutine. Alternatively, we could
        # have made this method async and used `await` before
        # returning
        return self._loop.run_in_executor(
            self._executor,
            functools.partial(func, *args, **kwargs),
        )


class AsyncioFile(AsyncExecutorBase):
    _path: pathlib.Path

    def __init__(self, path: pathlib.Path):
        super().__init__()
        self._path = path

    async def exists(self) -> bool:
        return await self._run_in_executor(self._path.exists)

    async def rename(self, target):
        return await self._run_in_executor(
            self._path.rename,
            target,
        )

    async def read_text(self, encoding=None, errors=None):
        return await self._run_in_executor(
            self._path.read_text,
            encoding=encoding,
            errors=errors,
        )

    async def read_bytes(self):
        return await self._run_in_executor(self._path.read_bytes)

    async def write_text(self, data, encoding=None, errors=None,
                         newline=None):
        return await self._run_in_executor(
            self._path.write_text,
            data,
            encoding=encoding,
            errors=errors,
            newline=newline,
        )

    async def write_bytes(self, data):
        return await self._run_in_executor(
            self._path.write_bytes,
            data,
        )

async def main():
    afile = AsyncioFile(pathlib.Path(__file__))

    print('#' * 79)
    print('Exists:', await afile.exists())
    print('#' * 79)
    print('Contents:')
    print(await afile.read_text())

if __name__ == '__main__':
    asyncio.run(main())
