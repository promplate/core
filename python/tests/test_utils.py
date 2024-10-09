from promplate.chain.utils import accumulate_any, resolve


async def test_resolve():
    async def f():
        return 1

    async def g():
        return f()

    async def h():
        return g()

    assert await resolve(h()) == 1


async def test_accumulate():
    it = accumulate_any("abc")
    assert await anext(it) == "a"
    assert await anext(it) == "ab"
    assert await anext(it) == "abc"
    await it.aclose()


async def test_accumulate_empty():
    async for _ in accumulate_any(""):
        assert False
