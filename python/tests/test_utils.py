from pytest import mark

from promplate.chain.utils import resolve


@mark.asyncio
async def test_resolve():
    async def f():
        return 1

    async def g():
        return f()

    async def h():
        return g()

    assert await resolve(h()) == 1
