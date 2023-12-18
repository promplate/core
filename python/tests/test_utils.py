from promplate.chain.utils import iterate, resolve


async def test_resolve():
    async def f():
        return 1

    async def g():
        return f()

    async def h():
        return g()

    assert await resolve(h()) == 1


async def test_iterate():
    async for i in iterate(range(1, 2)):
        assert i == 1

    async for i in iterate(iterate(range(1, 2))):
        assert i == 1
