from typing import AsyncIterable, Awaitable, Iterable, Protocol

from promplate.prompt.chat import Message


class CompleteText(Protocol):
    def __call__(self, text: str, **config) -> str:
        ...


class CompleteChat(Protocol):
    def __call__(self, messages: list[Message], **config) -> str:
        ...


class GenerateText(Protocol):
    def __call__(self, text: str, **config) -> Iterable[str]:
        ...


class GenerateChat(Protocol):
    def __call__(self, messages: list[Message], **config) -> Iterable[str]:
        ...


class AsyncCompleteText(Protocol):
    def __call__(self, text: str, **config) -> Awaitable[str]:
        ...


class AsyncCompleteChat(Protocol):
    def __call__(self, messages: list[Message], **config) -> Awaitable[str]:
        ...


class AsyncGenerateText(Protocol):
    def __call__(self, text: str, **config) -> AsyncIterable[str]:
        ...


class AsyncGenerateChat(Protocol):
    def __call__(self, messages: list[Message], **config) -> AsyncIterable[str]:
        ...


Complete = CompleteText | CompleteChat
Generate = GenerateText | GenerateChat

AsyncComplete = AsyncCompleteText | AsyncCompleteChat
AsyncGenerate = AsyncGenerateText | AsyncGenerateChat
