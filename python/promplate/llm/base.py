from typing import AsyncIterable, Awaitable, Iterable, Protocol


class Complete(Protocol):
    def __call__(self, text: str, /, **config) -> str:
        ...


class Generate(Protocol):
    def __call__(self, text: str, /, **config) -> Iterable[str]:
        ...


class AsyncComplete(Protocol):
    def __call__(self, text: str, /, **config) -> Awaitable[str]:
        ...


class AsyncGenerate(Protocol):
    def __call__(self, text: str, /, **config) -> AsyncIterable[str]:
        ...


# Backward compatibility

CompleteText = CompleteChat = Complete
GenerateText = GenerateChat = Generate
AsyncCompleteText = AsyncCompleteChat = AsyncComplete
AsyncGenerateText = AsyncGenerateChat = AsyncGenerate
