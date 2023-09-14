from typing import *

from promplate.prompt import Message

from . import base

class Configurable(base.Configurable):
    def __init__(
        self,
        *,
        model: str,
        temperature: float | int | None = None,
        top_p: float | int | None = None,
        stop: str | list[str] | None = None,
        max_tokens: int | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        **other_config,
    ):
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.stop = stop
        self.max_tokens = max_tokens
        self.api_key = api_key
        self.api_base = api_base

class TextComplete(Configurable, base.Complete):
    def __call__(
        self,
        text: str,
        /,
        **config,
    ) -> str: ...

class AsyncTextComplete(Configurable, base.AsyncComplete):
    def __call__(
        self,
        text: str,
        /,
        **config,
    ) -> Awaitable[str]: ...

class TextGenerate(Configurable, base.Generate):
    def __call__(
        self,
        text: str,
        /,
        **config,
    ) -> Iterable[str]: ...

class AsyncTextGenerate(Configurable, base.AsyncGenerate):
    def __call__(
        self,
        text: str,
        /,
        **config,
    ) -> AsyncIterable[str]: ...

class ChatComplete(Configurable, base.Complete):
    def __call__(
        self,
        messages: list[Message] | str,
        /,
        **config,
    ) -> str: ...

class AsyncChatComplete(Configurable, base.AsyncComplete):
    def __call__(
        self,
        messages: list[Message] | str,
        /,
        **config,
    ) -> Awaitable[str]: ...

class ChatGenerate(Configurable, base.Generate):
    def __call__(
        self,
        messages: list[Message] | str,
        /,
        **config,
    ) -> Iterable[str]: ...

class AsyncChatGenerate(Configurable, base.AsyncGenerate):
    def __call__(
        self,
        messages: list[Message] | str,
        /,
        **config,
    ) -> AsyncIterable[str]: ...

def text_complete(
    *,
    model: str,
    temperature: float | int | None = None,
    top_p: float | int | None = None,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    **other_config,
) -> TextComplete: ...
def async_text_complete(
    *,
    model: str,
    temperature: float | int | None = None,
    top_p: float | int | None = None,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    **other_config,
) -> AsyncTextComplete: ...
def text_generate(
    *,
    model: str,
    temperature: float | int | None = None,
    top_p: float | int | None = None,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    **other_config,
) -> TextGenerate: ...
def async_text_generate(
    *,
    model: str,
    temperature: float | int | None = None,
    top_p: float | int | None = None,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    **other_config,
) -> AsyncTextGenerate: ...
def chat_complete(
    *,
    model: str,
    temperature: float | int | None = None,
    top_p: float | int | None = None,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    **other_config,
) -> ChatComplete: ...
def async_chat_complete(
    *,
    model: str,
    temperature: float | int | None = None,
    top_p: float | int | None = None,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    **other_config,
) -> AsyncChatComplete: ...
def chat_generate(
    *,
    model: str,
    temperature: float | int | None = None,
    top_p: float | int | None = None,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    **other_config,
) -> ChatGenerate: ...
def async_chat_generate(
    *,
    model: str,
    temperature: float | int | None = None,
    top_p: float | int | None = None,
    stop: str | list[str] | None = None,
    max_tokens: int | None = None,
    api_key: str | None = None,
    api_base: str | None = None,
    **other_config,
) -> AsyncChatGenerate: ...
