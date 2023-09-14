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
) -> Complete: ...
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
) -> AsyncComplete: ...
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
) -> Generate: ...
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
) -> AsyncGenerate: ...
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
) -> Complete: ...
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
) -> AsyncComplete: ...
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
) -> Generate: ...
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
) -> AsyncGenerate: ...
