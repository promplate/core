from openai import ChatCompletion, Completion
from promplate.prompt.chat import Message

from .base import *


def text_complete(**default_config) -> CompleteText:
    def complete_text(text: str, **config):
        config = default_config | config | {"stream": False, "prompt": text}
        res = Completion.create(**config)
        return res["choices"][0]["text"]

    return complete_text


def async_text_complete(**default_config) -> AsyncCompleteText:
    async def async_complete_text(text: str, **config):
        config = default_config | config | {"stream": False, "prompt": text}
        res = await Completion.acreate(**config)
        return res["choices"][0]["text"]

    return async_complete_text


def chat_complete(**default_config) -> CompleteChat:
    def complete_chat(messages: list[Message], **config):
        config = default_config | config | {"stream": False, "messages": messages}
        res = ChatCompletion.create(messages=messages, **config)
        return res["choices"][0]["message"]["content"]

    return complete_chat


def async_chat_complete(**default_config) -> AsyncCompleteChat:
    async def async_complete_chat(messages: list[Message], **config):
        config = default_config | config | {"stream": False, "messages": messages}
        res = await ChatCompletion.acreate(messages=messages, **config)
        return res["choices"][0]["message"]["content"]

    return async_complete_chat
