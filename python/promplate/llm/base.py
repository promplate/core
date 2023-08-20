from typing import Awaitable, Callable

from promplate.prompt.chat import Message

CompleteText = Callable[[str], str]
CompleteChat = Callable[[list[Message]], str]
Complete = CompleteText | CompleteChat

AsyncCompleteText = Callable[[str], Awaitable[str]]
AsyncCompleteChat = Callable[[list[Message]], Awaitable[str]]
AsyncComplete = AsyncCompleteText | AsyncCompleteChat
