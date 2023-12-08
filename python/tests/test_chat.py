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
