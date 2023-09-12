from .base import *

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
) -> CompleteText: ...
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
) -> AsyncCompleteText: ...
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
) -> GenerateText: ...
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
) -> AsyncGenerateText: ...
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
) -> CompleteChat: ...
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
) -> AsyncCompleteChat: ...
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
) -> GenerateChat: ...
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
) -> AsyncGenerateChat: ...
