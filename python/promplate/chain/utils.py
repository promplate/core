from inspect import Parameter, isasyncgen, isawaitable, signature
from typing import AsyncIterable, Awaitable, Callable, Iterable, List, TypeVar, Union

T = TypeVar("T")


def appender(to_append: List[T]) -> Callable[[T], T]:
    def append_processer(func: T) -> T:
        to_append.append(func)

        return func

    return append_processer


def is_positional_parameter(p: Parameter):
    return p.kind is Parameter.POSITIONAL_OR_KEYWORD or p.kind is Parameter.KEYWORD_ONLY


def count_position_parameters(func):
    return sum(map(is_positional_parameter, signature(func).parameters.values()))


async def resolve(maybe_awaitable: Union[T, Awaitable[T]], /) -> T:
    while isawaitable(maybe_awaitable):
        maybe_awaitable = await maybe_awaitable

    return maybe_awaitable  # type: ignore


async def iterate(maybe_asyncgen: Union[Iterable, AsyncIterable]):
    if isasyncgen(maybe_asyncgen):
        async for i in maybe_asyncgen:
            yield i
    else:
        for i in maybe_asyncgen:  # type: ignore
            yield i
