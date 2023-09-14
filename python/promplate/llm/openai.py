from openai import ChatCompletion, Completion
from promplate.prompt.chat import Message, parse_chat_markup

from .base import *


def text_complete(**default_config) -> Complete:
    def complete_text(text: str, /, **config):
        config = default_config | config | {"stream": False, "prompt": text}
        result = Completion.create(**config)
        return result["choices"][0]["text"]

    return complete_text


def async_text_complete(**default_config) -> AsyncComplete:
    async def async_complete_text(text: str, /, **config):
        config = default_config | config | {"stream": False, "prompt": text}
        result = await Completion.acreate(**config)
        return result["choices"][0]["text"]

    return async_complete_text


def text_generate(**default_config) -> Generate:
    def generate_text(text: str, /, **config):
        config = default_config | config | {"stream": True, "prompt": text}
        stream = Completion.create(**config)
        for event in stream:
            yield event["choices"][0]["text"]

    return generate_text


def async_text_generate(**default_config) -> AsyncGenerate:
    async def async_generate_text(text: str, /, **config):
        config = default_config | config | {"stream": True, "prompt": text}
        stream = await Completion.acreate(**config)
        async for event in stream:
            yield event["choices"][0]["text"]

    return async_generate_text


def chat_complete(**default_config) -> Complete:
    def complete_chat(messages: list[Message] | str, /, **config):
        messages = _ensure(messages)
        config = default_config | config | {"stream": False, "messages": messages}
        result = ChatCompletion.create(**config)
        return result["choices"][0]["message"]["content"]

    return complete_chat


def async_chat_complete(**default_config) -> AsyncComplete:
    async def async_complete_chat(messages: list[Message] | str, /, **config):
        messages = _ensure(messages)
        config = default_config | config | {"stream": False, "messages": messages}
        result = await ChatCompletion.acreate(**config)
        return result["choices"][0]["message"]["content"]

    return async_complete_chat


def chat_generate(**default_config) -> Generate:
    def generate_chat(messages: list[Message] | str, /, **config):
        messages = _ensure(messages)
        config = default_config | config | {"stream": True, "messages": messages}
        stream = ChatCompletion.create(**config)
        for event in stream:
            delta: dict = event["choices"][0]["delta"]
            yield delta.get("content", "")

    return generate_chat


def async_chat_generate(**default_config) -> AsyncGenerate:
    async def async_generate_chat(messages: list[Message] | str, /, **config):
        messages = _ensure(messages)
        config = default_config | config | {"stream": True, "messages": messages}
        stream = await ChatCompletion.acreate(**config)
        async for event in stream:
            delta: dict = event["choices"][0]["delta"]
            yield delta.get("content", "")

    return async_generate_chat


def _ensure(text_or_list: list[Message] | str) -> list[Message]:
    return (
        parse_chat_markup(text_or_list)
        if isinstance(text_or_list, str)
        else text_or_list
    )
