from promplate.prompt.chat import Message, parse_chat_markup


def ensure(text_or_list: list[Message] | str) -> list[Message]:
    return (
        parse_chat_markup(text_or_list)
        if isinstance(text_or_list, str)
        else text_or_list
    )
