from sys import version_info
from typing import Literal

from .utils import is_message_start

Role = Literal["user", "assistant", "system"]

if version_info >= (3, 12):
    from typing import NotRequired, TypedDict

    class Message(TypedDict):  # type: ignore
        role: Role
        content: str
        name: NotRequired[str]

else:
    from typing_extensions import NotRequired, TypedDict

    class Message(TypedDict):
        role: Role
        content: str
        name: NotRequired[str]


class MessageBuilder:
    _initializing = True
    __slots__ = ("role", "content", "name")

    def __init__(self, role: Role, /, content: str = "", name: str | None = None):
        self.role: Role = role
        self.content = content
        self.name = name

    def __repr__(self):
        if self.name is not None:
            return f"<| {self.role} {self.name} |>"
        return f"<| {self.role} |>"

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __setattr__(self, key, value):
        if not self._initializing:
            assert self is not U and self is not A and self is not S
            assert isinstance(value, str)
        return super().__setattr__(key, value)

    def __matmul__(self, name: str):
        assert isinstance(name, str) and name
        return self.__class__(self.role, self.content, name)

    def dict(self) -> Message:
        if self.name:
            return {"role": self.role, "content": self.content, "name": self.name}
        return {"role": self.role, "content": self.content}

    def __gt__(self, content: str) -> Message:
        assert isinstance(content, str)
        if self.name:
            return {"role": self.role, "content": content, "name": self.name}
        return {"role": self.role, "content": content}


U = user = MessageBuilder("user")
A = assistant = MessageBuilder("assistant")
S = system = MessageBuilder("system")
MessageBuilder._initializing = False


def ensure(text_or_list: list[Message] | str) -> list[Message]:
    return parse_chat_markup(text_or_list) if isinstance(text_or_list, str) else text_or_list


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

    if messages:
        return messages
    elif text and text != "\n":
        return [{"role": "user", "content": text.removesuffix("\n")}]
    return []
