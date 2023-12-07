from inspect import Parameter, isawaitable, signature
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


def appender(to_append: list[T]) -> Callable[[T], T]:
    def append_processer(func: T) -> T:
        to_append.append(func)

        return func

    return append_processer


def is_positional_parameter(p: Parameter):
    return p.kind is Parameter.POSITIONAL_OR_KEYWORD or p.kind is Parameter.KEYWORD_ONLY


def count_position_parameters(func):
    return sum(map(is_positional_parameter, signature(func).parameters.values()))


async def resolve(maybe_awaitable: T | Awaitable[T], /) -> T:
    while isawaitable(maybe_awaitable):
        maybe_awaitable = await maybe_awaitable

    return maybe_awaitable  # type: ignore
