from openai import ChatCompletion, Completion
from promplate.prompt.chat import Message

from .base import *


def text_complete(**default_config) -> CompleteText:
    def complete_text(text: str, **config):
        config = default_config | config | {"stream": False, "prompt": text}
        result = Completion.create(**config)
        return result["choices"][0]["text"]

    return complete_text


def async_text_complete(**default_config) -> AsyncCompleteText:
    async def async_complete_text(text: str, **config):
        config = default_config | config | {"stream": False, "prompt": text}
        result = await Completion.acreate(**config)
        return result["choices"][0]["text"]

    return async_complete_text


def text_generate(**default_config) -> GenerateText:
    def generate_text(text: str, **config):
        config = default_config | config | {"stream": True, "prompt": text}
        stream = Completion.create(**config)
        for event in stream:
            yield event["choices"][0]["text"]

    return generate_text


def async_text_generate(**default_config) -> AsyncGenerateText:
    async def async_generate_text(text: str, **config):
        config = default_config | config | {"stream": True, "prompt": text}
        stream = Completion.acreate(**config)
        async for event in stream:
            yield event["choices"][0]["text"]

    return async_generate_text


def chat_complete(**default_config) -> CompleteChat:
    def complete_chat(messages: list[Message], **config):
        config = default_config | config | {"stream": False, "messages": messages}
        result = ChatCompletion.create(**config)
        return result["choices"][0]["message"]["content"]

    return complete_chat


def async_chat_complete(**default_config) -> AsyncCompleteChat:
    async def async_complete_chat(messages: list[Message], **config):
        config = default_config | config | {"stream": False, "messages": messages}
        result = await ChatCompletion.acreate(**config)
        return result["choices"][0]["message"]["content"]

    return async_complete_chat


def chat_generate(**default_config) -> GenerateChat:
    def generate_chat(messages: list[Message], **config):
        config = default_config | config | {"stream": True, "messages": messages}
        stream = ChatCompletion.create(**config)
        for event in stream:
            delta: dict = event["choices"][0]["delta"]
            yield delta.get("content", "")

    return generate_chat


def async_chat_generate(**default_config) -> AsyncGenerateChat:
    async def async_generate_chat(messages: list[Message], **config):
        config = default_config | config | {"stream": True, "messages": messages}
        stream = ChatCompletion.acreate(**config)
        async for event in stream:
            delta: dict = event["choices"][0]["delta"]
            yield delta.get("content", "")

    return async_generate_chat
