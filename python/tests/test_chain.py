from typing import cast

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

    @b.mid_process
    def _(_):
        nonlocal chain
        chain += c

    assert chain.invoke(complete=as_is).result == "abc"


def test_chain_break():
    a = Node("0")
    b = Node("1")

    chain = a + b

    @a.mid_process
    def _(_):
        raise Jump(bubble_up_to=chain)

    assert chain.invoke(complete=as_is).result == "0"


def test_loop_break():
    a = Node("0")
    b = Node("{{ int(__result__) + 1 }}")

    @b.mid_process
    def _(context: ChainContext):
        if int(context.result) >= 6:
            raise Jump(bubble_up_to=chain)

    chain = a + Loop(b)

    assert chain.invoke(complete=as_is).result == "6"


def test_chain_callback():
    a = Node("0")
    b = Node("{{ int(__result__) + 1 }}")

    chain = a + b + b + b

    @chain.mid_process
    def _(context: ChainContext):
        if context.result:
            context["sum"] = context.get("sum", 0) + int(context.result)

    assert chain.invoke(complete=as_is).result == str(0 + 1 + 2)


def test_processes():
    node = Node("")

    @node.mid_process
    def _(context: ChainContext):
        cast(list, context["results"]).append(context.result)

    @node.end_process
    def _(context: ChainContext):
        cast(list, context["results"]).append("end")

    def zero_to_three(_, **config):
        yield from map(str, range(4))

    list(node.stream(context := {"results": []}, zero_to_three))
    assert context["results"] == ["0", "01", "012", "0123", "end"]
