from promplate import Chain, ChainContext, Node
from promplate.chain.node import JumpTo, Loop


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


def test_loop_break():
    a = Node("0")
    b = Node("{{ int(__result__) + 1 }}")
    c = Node("{{ __result__ }}" * 3)

    @b.post_process
    def _(context: ChainContext):
        if int(context.result) >= 6:
            raise JumpTo(c, bubble_up_to=chain)

    chain = a + Loop(b)

    assert chain.invoke(complete=as_is).result == "666"
