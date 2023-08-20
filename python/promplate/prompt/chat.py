from typing import Literal, TypedDict

from .template import Template
from .utils import is_message_start

Message = TypedDict(
    "Message",
    {"role": Literal["user", "assistant", "system"], "content": str, "name": str},
    total=False,
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

    return messages


class ChatTemplate(Template):
    def render(self, context):
        return parse_chat_markup(super().render(context))

    async def arender(self, context):
        return parse_chat_markup(await super().arender(context))
