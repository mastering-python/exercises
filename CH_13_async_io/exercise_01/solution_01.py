import asyncio


class AsyncMeta(type):

    def __new__(mcs, name, bases, namespace):
        cls = type.__new__(mcs, name, bases, namespace)
        cls._instances = []
        origin_new = cls.__new__

        def __new__(cls, *args, **kwargs):
            ins = origin_new(cls, *args, **kwargs)
            cls._instances.append(ins)
            return ins

        cls.__new__ = __new__
        return cls

    async def close_all(cls):
        while cls._instances:
            await cls._instances.pop().close()

    async def __aenter__(cls):
        return cls

    async def __aexit__(cls, exc_type, exc_val, exc_tb):
        await cls.close_all()

    def __del__(cls):
        asyncio.run(cls.close_all())


class AsyncClass(metaclass=AsyncMeta):

    def __init__(self):
        self.name = None

    async def init(self, name):
        self.name = name
        print(f'init {name}')

    @classmethod
    async def create(cls, name):
        ins = cls()
        await ins.init(name)
        return ins

    async def close(self):
        print(f'close {self.name}')


async def main():
    global AsyncClass
    print('Using close method directly')
    egg = await AsyncClass.create('egg')
    spam = await AsyncClass.create('spam')
    await AsyncClass.close_all()

    print()

    print('Using async with')
    async with AsyncClass:
        egg = await AsyncClass.create('egg')
        spam = await AsyncClass.create('spam')

    print()

    print('Using __del__')
    egg = await AsyncClass.create('egg')
    spam = await AsyncClass.create('spam')
    # del AsyncClass


if __name__ == '__main__':
    asyncio.run(main())
