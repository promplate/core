from operator import setitem

from pytest import raises

from promplate import Node
from promplate.chain.callback import Callback


def test_add_callback_by_lambda():
    node = Node("{{ a }}")

    with raises(NameError):
        node.render()

    node.callbacks.append(Callback(pre_process=lambda x: setitem(x, "a", 1)))

    assert node.render() == "1"


def test_add_callback_by_class_1():
    node = Node("{{ b }}")

    @node.callback
    class _(Callback):
        def pre_process(self, context):
            context["b"] = 2

    assert node.render() == "2"


def test_add_callback_by_class_2():
    node = Node("{{ b }}")

    @node.callback
    class _(Callback):
        def pre_process(self, context):
            return {"b": 2}

    assert node.render() == "2"


def test_node_invoke():
    node = Node("{{ a }}")

    complete = lambda prompt, **_: prompt

    assert node.invoke({"a": 1}, complete).result == "1"


def test_context_behavior():
    a = Node("{{ a }}", {"a": 1})
    b = Node("{{ b }}")
    chain = a + b
    chain.context["a"] = 2
    chain.context["b"] = 3
    it = iter(chain.stream({"a": 4}, lambda prompt, **_: prompt))

    assert next(it).result == "4"
    assert next(it).result == "3"