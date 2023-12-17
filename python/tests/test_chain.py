from promplate import Chain, ChainContext, Jump, Loop, Node


def as_is(prompt: str, **_):
    return prompt


def test_chain_partial_context():
    a = Node("{{ a }}")
    b = Node("{{ __result__ }}{{ b }}")
    c = Chain(a, b, partial_context={"a": "A", "b": "B"})
    assert c.invoke(complete=as_is).result == "AB"


def test_chain_ior():
    a = Node("a")
    b = Node("{{ __result__ }}b")
    c = Node("{{ __result__ }}c")

    chain = a + b

    @b.post_process
    def _(_):
        nonlocal chain
        chain += c

    assert chain.invoke(complete=as_is).result == "abc"


def test_chain_break():
    a = Node("0")
    b = Node("1")

    chain = a + b

    @a.post_process
    def _(_):
        raise Jump(bubble_up_to=chain)

    assert chain.invoke(complete=as_is).result == "0"


def test_loop_break():
    a = Node("0")
    b = Node("{{ int(__result__) + 1 }}")

    @b.post_process
    def _(context: ChainContext):
        if int(context.result) >= 6:
            raise Jump(bubble_up_to=chain)

    chain = a + Loop(b)

    assert chain.invoke(complete=as_is).result == "6"
