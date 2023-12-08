from pytest import raises

from promplate.prompt.chat import A, S, U, parse_chat_markup


def test_builder_roles():
    assert A.role == "assistant"
    assert S.role == "system"
    assert U.role == "user"


def test_builder_names():
    assert A.name is None
    assert (S @ "name").name == "name"
    assert (U @ "name" > "text")["name"] == "name"  # type: ignore


def test_chat_markup():
    assert parse_chat_markup("hi") == [U > "hi"]
    assert parse_chat_markup("<| user name |>") == [U @ "name" > ""]
    assert parse_chat_markup("123\n234\n\n345") == [U > "123\n234\n\n345"]
    assert parse_chat_markup("<|user|>\n123\n<|assistant|>\n456") == [U > "123", A > "456"]


def test_auto_trim_trailing_blank_line():
    assert [U > "123"] == parse_chat_markup("123")
    assert [U > "123"] == parse_chat_markup("123\n")
    assert [U > "123"] == parse_chat_markup("<|user|>\n123")
    assert [U > "123"] == parse_chat_markup("<|user|>\n123\n")


def test_immutable_constants():
    with raises(AssertionError):
        A.content = "content"
