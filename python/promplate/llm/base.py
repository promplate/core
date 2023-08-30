from typing import Any, AsyncIterator, Awaitable, Callable, Iterator

from promplate.prompt.chat import Message

CompleteText = Callable[[str, Any], str]
CompleteChat = Callable[[list[Message], Any], str]
GenerateText = Callable[[str, Any], Iterator[str]]
GenerateChat = Callable[[list[Message], Any], Iterator[str]]
Complete = CompleteText | CompleteChat
Generate = GenerateText | GenerateChat

AsyncCompleteText = Callable[[str, Any], Awaitable[str]]
AsyncCompleteChat = Callable[[list[Message], Any], Awaitable[str]]
AsyncGenerateText = Callable[[str, Any], AsyncIterator[str]]
AsyncGenerateChat = Callable[[list[Message], Any], AsyncIterator[str]]
AsyncComplete = AsyncCompleteText | AsyncCompleteChat
AsyncGenerate = AsyncGenerateText | AsyncGenerateChat
