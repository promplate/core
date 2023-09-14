from importlib.metadata import metadata

import openai
from openai import ChatCompletion, Completion

from .base import *
from .utils import Message, ensure

meta = metadata("promplate")

openai.app_info = {
    "name": "Promplate",
    "version": meta["version"],
    "url": meta["home-page"],
}


class TextComplete(Configurable, Complete):
    def __call__(self, text, /, **config):
        config = self._config | config | {"stream": False, "prompt": text}
        result = Completion.create(**config)
        return result["choices"][0]["text"]


class AsyncTextComplete(Configurable, AsyncComplete):
    async def __call__(self, text, /, **config):
        config = self._config | config | {"stream": False, "prompt": text}
        result = await Completion.acreate(**config)
        return result["choices"][0]["text"]


class TextGenerate(Configurable, Generate):
    def __call__(self, text, /, **config):
        config = self._config | config | {"stream": True, "prompt": text}
        stream = Completion.create(**config)
        for event in stream:
            yield event["choices"][0]["text"]


class AsyncTextGenerate(Configurable, AsyncGenerate):
    async def __call__(self, text, /, **config):
        config = self._config | config | {"stream": True, "prompt": text}
        stream = await Completion.acreate(**config)
        async for event in stream:
            yield event["choices"][0]["text"]


class ChatComplete(Configurable, Complete):
    def __call__(self, messages: list[Message] | str, /, **config):
        messages = ensure(messages)
        config = self._config | config | {"stream": False, "messages": messages}
        result = ChatCompletion.create(**config)
        return result["choices"][0]["message"]["content"]


class AsyncChatComplete(Configurable, AsyncComplete):
    async def __call__(self, messages: list[Message] | str, /, **config):
        messages = ensure(messages)
        config = self._config | config | {"stream": False, "messages": messages}
        result = await ChatCompletion.acreate(**config)
        return result["choices"][0]["message"]["content"]


class ChatGenerate(Configurable, Generate):
    def __call__(self, messages: list[Message] | str, /, **config):
        messages = ensure(messages)
        config = self._config | config | {"stream": True, "messages": messages}
        stream = ChatCompletion.create(**config)
        for event in stream:
            delta: dict = event["choices"][0]["delta"]
            yield delta.get("content", "")


class AsyncChatGenerate(Configurable, AsyncGenerate):
    async def __call__(self, messages: list[Message] | str, /, **config):
        messages = ensure(messages)
        config = self._config | config | {"stream": True, "messages": messages}
        stream = await ChatCompletion.acreate(**config)
        async for event in stream:
            delta: dict = event["choices"][0]["delta"]
            yield delta.get("content", "")


def text_complete(**default_config):
    return TextComplete(**default_config)


def async_text_complete(**default_config):
    return AsyncTextComplete(**default_config)


def text_generate(**default_config):
    return TextGenerate(**default_config)


def async_text_generate(**default_config):
    return AsyncTextGenerate(**default_config)


def chat_complete(**default_config):
    return ChatComplete(**default_config)


def async_chat_complete(**default_config):
    return AsyncChatComplete(**default_config)


def chat_generate(**default_config):
    return ChatGenerate(**default_config)


def async_chat_generate(**default_config):
    return AsyncChatGenerate(**default_config)
