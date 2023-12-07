from functools import cached_property
from typing import Any, Callable, ParamSpec, TypeVar

from openai import AsyncClient, Client  # type: ignore

from ...prompt.chat import Message, ensure
from ..base import *

P = ParamSpec("P")
T = TypeVar("T")


def same_params_as(_: Callable[P, Any]):
    def func(cls: type[T]) -> Callable[P, T]:
        return cls  # type: ignore

    return func


class ClientConfig(Configurable):
    @same_params_as(Client)  # type: ignore
    def __init__(self, **config):
        super().__init__(**config)

    @cached_property
    def client(self):
        return Client(**self._config)

    @cached_property
    def aclient(self):
        return AsyncClient(**self._config)


class TextComplete(ClientConfig):
    def __call__(self, text: str, /, **config):
        config = config | {"stream": False, "prompt": text}
        result = self.client.completions.create(**config)
        return result.choices[0].text


class AsyncTextComplete(ClientConfig):
    async def __call__(self, text: str, /, **config):
        config = config | {"stream": False, "prompt": text}
        result = await self.aclient.completions.create(**config)
        return result.choices[0].text


class TextGenerate(ClientConfig):
    def __call__(self, text: str, /, **config):
        config = config | {"stream": True, "prompt": text}
        stream = self.client.completions.create(**config)
        for event in stream:
            yield event.choices[0].text


class AsyncTextGenerate(ClientConfig):
    async def __call__(self, text: str, /, **config):
        config = config | {"stream": True, "prompt": text}
        stream = await self.aclient.completions.create(**config)
        async for event in stream:
            yield event.choices[0].text


class ChatComplete(ClientConfig):
    def __call__(self, messages: list[Message] | str, /, **config):
        messages = ensure(messages)
        config = config | {"stream": False, "messages": messages}
        result = self.client.chat.completions.create(**config)
        return result.choices[0].message.content


class AsyncChatComplete(ClientConfig):
    async def __call__(self, messages: list[Message] | str, /, **config):
        messages = ensure(messages)
        config = config | {"stream": False, "messages": messages}
        result = await self.aclient.chat.completions.create(**config)
        return result.choices[0].message.content


class ChatGenerate(ClientConfig):
    def __call__(self, messages: list[Message] | str, /, **config):
        messages = ensure(messages)
        config = config | {"stream": True, "messages": messages}
        stream = self.client.chat.completions.create(**config)
        for event in stream:
            yield event.choices[0].delta.content or ""


class AsyncChatGenerate(ClientConfig):
    async def __call__(self, messages: list[Message] | str, /, **config):
        messages = ensure(messages)
        config = config | {"stream": True, "messages": messages}
        stream = await self.aclient.chat.completions.create(**config)
        async for event in stream:
            yield event.choices[0].delta.content or ""


class SyncTextOpenAI(ClientConfig):
    complete = TextComplete.__call__
    generate = TextGenerate.__call__


class AsyncTextOpenAI(ClientConfig):
    complete = AsyncTextComplete.__call__
    generate = AsyncTextGenerate.__call__


class SyncChatOpenAI(ClientConfig):
    complete = ChatComplete.__call__
    generate = ChatGenerate.__call__


class AsyncChatOpenAI(ClientConfig):
    complete = AsyncChatComplete.__call__
    generate = AsyncChatGenerate.__call__
