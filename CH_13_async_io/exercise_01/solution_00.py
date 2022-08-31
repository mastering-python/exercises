# Try to create a `asyncio` base class that automatically
# registers all instances for easy closing/destructuring when you
# are done
import abc
import asyncio


class AsyncBase(abc.ABC):
    _instances = []

    def __init__(self):
        self._instances.append(self)

    async def close(self):
        raise NotImplementedError


class AsyncManager(AsyncBase):
    # Use a separate class for the managing of the instances so
    # we don't pollute the namespace of the base class

    @classmethod
    async def close(cls):
        # Make sure to clear the list of instances while closing
        while cls._instances:
            await cls._instances.pop().close()

    # Support `async with` syntax as well
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()


class A(AsyncBase):
    def __init__(self):
        super().__init__()
        print('A.__init__')

    async def close(self):
        print('A.close')


class B(AsyncBase):
    def __init__(self):
        super().__init__()
        print('B.__init__')

    async def close(self):
        print('B.close')


async def main():
    print('Using close method directly')

    A()
    B()
    await AsyncManager.close()

    print()


async def main_with():
    print('Using async with')

    async with AsyncManager():
        A()
        B()

    print()


if __name__ == '__main__':
    asyncio.run(main())
    asyncio.run(main_with())
