from inspect import Parameter, isasyncgen, isawaitable, signature
from itertools import accumulate
from typing import AsyncIterable, Awaitable, Callable, Iterable, List, TypeVar, Union, cast

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


async def async_accumulate(async_iterable: AsyncIterable[str]):
    result = ""
    async for delta in async_iterable:
        result += delta
        yield result


def accumulate_any(any_iterable: Union[Iterable[str], AsyncIterable[str]]):
    if isasyncgen(any_iterable):
        return async_accumulate(any_iterable)

    async def _():
        for i in accumulate(cast(Iterable[str], any_iterable)):
            yield i

    return _()
