from typing import AsyncIterator, Awaitable, Callable, Iterator

from promplate.prompt.chat import Message

CompleteText = Callable[[str], str]
CompleteChat = Callable[[list[Message]], str]
GenerateText = Callable[[str], Iterator[str]]
GenerateChat = Callable[[list[Message]], Iterator[str]]
Complete = CompleteText | CompleteChat
Generate = GenerateText | GenerateChat

AsyncCompleteText = Callable[[str], Awaitable[str]]
AsyncCompleteChat = Callable[[list[Message]], Awaitable[str]]
AsyncGenerateText = Callable[[str], AsyncIterator[str]]
AsyncGenerateChat = Callable[[list[Message]], AsyncIterator[str]]
AsyncComplete = AsyncCompleteText | AsyncCompleteChat
AsyncGenerate = AsyncGenerateText | AsyncGenerateChat
