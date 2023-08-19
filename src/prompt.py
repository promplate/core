from .utils import is_message_start


def parse_text(text: str):
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


class Prompt:
    def __init__(self, messages):
        self.messages = messages

    @classmethod
    def from_text(cls, text):
        return cls(parse_text(text))
