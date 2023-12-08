from typing import AsyncIterable, Awaitable, Iterable, Protocol


class Configurable:
    def __init__(self, **config):
        for key, val in config.items():
            setattr(self, key, val)

    @property
    def _config(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}


class Complete(Protocol):
    def __call__(self, prompt, /, **config) -> str:
        ...


class Generate(Protocol):
    def __call__(self, prompt, /, **config) -> Iterable[str]:
        ...


class AsyncComplete(Protocol):
    def __call__(self, prompt, /, **config) -> Awaitable[str]:
        ...


class AsyncGenerate(Protocol):
    def __call__(self, prompt, /, **config) -> AsyncIterable[str]:
        ...


class LLM(Protocol):
    complete: Complete | AsyncComplete
    generate: Generate | AsyncGenerate
