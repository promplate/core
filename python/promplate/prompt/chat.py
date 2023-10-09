from sys import version_info
from typing import Literal

from .utils import is_message_start

if version_info >= (3, 11):
    from typing import NotRequired, TypedDict
else:
    from typing_extensions import NotRequired, TypedDict


class Message(TypedDict):
    role: Literal["user", "assistant", "system"]
    content: str
    name: NotRequired[str]


def ensure(text_or_list: list[Message] | str) -> list[Message]:
    return (
        parse_chat_markup(text_or_list)
        if isinstance(text_or_list, str)
        else text_or_list
    )


def parse_chat_markup(text: str) -> list[Message]:
    messages = []
    current_message = None
    buffer = []

    for line in text.splitlines():
        match = is_message_start.match(line)
        if match:
            role, name = match.group(1), match.group(2)

            if current_message:
                current_message["content"] = "\n".join(buffer)
                messages.append(current_message)
                buffer.clear()

            current_message = {"role": role, "content": ""}

            if name:
                current_message["name"] = name

        elif current_message:
            buffer.append(line)

    if current_message:
        current_message["content"] = "\n".join(buffer)
        messages.append(current_message)

    return messages or [{"role": "user", "content": text}]
