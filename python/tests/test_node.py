from operator import setitem

from pytest import raises

from promplate import BaseCallback, Callback, ChainContext, Node


def test_add_callback_by_lambda():
    node = Node("{{ a }}")

    with raises(NameError):
        node.render()

    node.callbacks.append(Callback(pre_process=lambda x: setitem(x, "a", 1)))

    assert node.render() == "1"


def test_add_callback_by_decorator_1():
    node = Node("{{ b }}")

    @node.callback
    class _(BaseCallback):
        def pre_process(self, context):
            context["b"] = 2

    assert node.render() == "2"


def test_add_callback_by_decorator_2():
    node = Node("{{ b }}")

    @node.callback
    class _(BaseCallback):
        def pre_process(self, context):
            return {"b": 2}

    assert node.render() == "2"


def test_node_invoke():
    node = Node("{{ a }}")
    complete = lambda prompt, **_: prompt
    assert node.invoke({"a": 1}, complete).result == "1"


async def test_node_ainvoke():
    node = Node("{{ b }}")
    complete = lambda prompt, **_: prompt
    assert (await node.ainvoke({"b": 2}, complete)).result == "2"


def test_node_stream():
    node = Node("{{ nums }}")

    def generate(prompt, **_):
        yield from prompt

    for i, context in enumerate(node.stream({"nums": 1234}, generate), 1):
        assert i == int(context.result[-1])


async def test_node_astream():
    node = Node("{{ nums }}")

    async def generate(prompt, **_):
        for i in prompt:
            yield i

    assert [int(i.result) async for i in node.astream({"nums": 123}, generate)] == [1, 12, 123]


def test_context_behavior():
    a = Node("{{ a }}", {"a": 1})
    b = Node("{{ b }}")
    chain = a + b
    chain.context["a"] = 2
    chain.context["b"] = 3
    it = iter(chain.stream({"a": 4}, lambda prompt, **_: prompt))

    assert next(it).result == "4"
    assert next(it).result == "3"


def test_callbacks_with_states():
    chain = Node("")

    @chain.callback
    class _(BaseCallback):
        def on_enter(self, node, context, config):
            context = {} if context is None else context
            self.entered = True
            return context, config

        def pre_process(self, context):
            assert self.entered

    with raises(AttributeError):
        chain.render()

    assert chain.invoke(complete=lambda prompt, **_: prompt).result == ""


def test_order_of_callbacks():
    node = Node("ABC")

    def generate(prompt: str, /, **config):
        yield from prompt

    @node.callback
    class Add1(BaseCallback):
        def mid_process(self, context: ChainContext):
            return {"letters": context.get("letters", []) + [f"{context.result}1"]}

        def end_process(self, context: ChainContext):
            return {"letters": context.get("letters", []) + ["end1"]}

    @node.callback
    class Add2(BaseCallback):
        def mid_process(self, context: ChainContext):
            return {"letters": context.get("letters", []) + [f"{context.result}2"]}

        def end_process(self, context: ChainContext):
            return {"letters": context.get("letters", []) + ["end2"]}

    list(node.stream(context := {}, generate))
    assert context["letters"] == ["A1", "A2", "AB1", "AB2", "ABC1", "ABC2", "end2", "end1"]


def test_config_overwrite():
    node = Node("")
    node.run_config["key"] = "1"
    assert node.invoke(complete=lambda _, key: key, key="2").result == "2"  # type: ignore
