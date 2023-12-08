from collections import ChainMap
from typing import TYPE_CHECKING, Callable, Mapping, MutableMapping, TypeVar, overload

from ..llm.base import *
from ..llm.base import AsyncGenerate, AsyncIterable, Generate, Iterable
from ..prompt.template import Context, Loader, Template
from .callback import AbstractCallback, Callback
from .utils import appender, resolve


class ChainContext(ChainMap, dict):
    @overload
    def __init__(self):
        ...

    @overload
    def __init__(self, least: MutableMapping | None = None):
        ...

    @overload
    def __init__(self, least: MutableMapping | None = None, *maps: Mapping):
        ...

    def __init__(self, least: MutableMapping | None = None, *maps: Mapping):
        super().__init__({} if least is None else least, *maps)  # type: ignore

    @classmethod
    def ensure(cls, context):
        return context if isinstance(context, cls) else cls(context)

    @property
    def result(self):
        return self.__getitem__("__result__")

    @result.setter
    def result(self, result):
        self.__setitem__("__result__", result)

    @result.deleter
    def result(self):
        self.__delitem__("__result__")

    if TYPE_CHECKING:  # fix type from `collections.ChainMap`
        from sys import version_info

        if version_info >= (3, 11):
            from typing_extensions import Self
        else:
            from typing import Self

        copy: Callable[[Self], Self]


CTX = TypeVar("CTX", Context, ChainContext)


Process = Callable[[CTX], CTX | None]

AsyncProcess = Callable[[CTX], Awaitable[CTX | None]]


class AbstractChain(Protocol):
    def invoke(
        self,
        context: Context | None = None,
        /,
        complete: Complete | None = None,
    ) -> ChainContext:
        ...

    async def ainvoke(
        self,
        context: Context | None = None,
        /,
        complete: Complete | AsyncComplete | None = None,
    ) -> ChainContext:
        ...

    def stream(
        self,
        context: Context | None = None,
        /,
        generate: Generate | None = None,
    ) -> Iterable[ChainContext]:
        ...

    def astream(
        self,
        context: Context | None = None,
        /,
        generate: Generate | AsyncGenerate | None = None,
    ) -> AsyncIterable[ChainContext]:
        ...


class Interruptable(AbstractChain, Protocol):
    def _invoke(
        self,
        context: ChainContext,
        /,
        complete: Complete | None = None,
    ):
        ...

    async def _ainvoke(
        self,
        context: ChainContext,
        /,
        complete: Complete | AsyncComplete | None = None,
    ):
        ...

    def _stream(
        self,
        context: ChainContext,
        /,
        generate: Generate | None = None,
    ) -> Iterable:
        ...

    def _astream(
        self,
        context: ChainContext,
        /,
        generate: Generate | AsyncGenerate | None = None,
    ) -> AsyncIterable:
        ...

    def invoke(self, context=None, /, complete=None) -> ChainContext:
        context = ChainContext.ensure(context)

        try:
            self._invoke(ChainContext(context, self.context), complete)
        except JumpTo as jump:
            if jump.target is None or jump.target is self:
                jump.chain.invoke(context, complete)
            else:
                raise jump from None

        return context

    async def ainvoke(self, context=None, /, complete=None) -> ChainContext:
        context = ChainContext.ensure(context)

        try:
            await self._ainvoke(ChainContext(context, self.context), complete)
        except JumpTo as jump:
            if jump.target is None or jump.target is self:
                await jump.chain.ainvoke(context, complete)
            else:
                raise jump from None

        return context

    def stream(self, context=None, /, generate=None) -> Iterable[ChainContext]:
        context = ChainContext.ensure(context)

        try:
            for _ in self._stream(ChainContext(context, self.context), generate):
                yield context
        except JumpTo as jump:
            if jump.target is None or jump.target is self:
                yield from jump.chain.stream(context, generate)
            else:
                raise jump from None

    async def astream(self, context=None, /, generate=None) -> AsyncIterable[ChainContext]:
        context = ChainContext.ensure(context)

        try:
            async for _ in self._astream(ChainContext(context, self.context), generate):
                yield context
        except JumpTo as jump:
            if jump.target is None or jump.target is self:
                async for i in jump.chain.astream(context, generate):
                    yield i
            else:
                raise jump from None

    _context: Context | None

    @property
    def context(self):
        if self._context is None:
            self._context = {}
        return self._context

    @context.setter
    def context(self, context: Context | None):
        self._context = context

    @context.deleter
    def context(self):
        self._context = None


class Node(Loader, Interruptable):
    def __init__(
        self,
        template: Template | str,
        partial_context: Context | None = None,
        llm: LLM | None = None,
        **config,
    ):
        self.template = Template(template) if isinstance(template, str) else template
        self._context = partial_context
        self.callbacks: list[AbstractCallback] = []
        self.llm = llm
        self.run_config = config

    def add_pre_processes(self, *processes: Process | AsyncProcess):
        self.callbacks.extend(Callback(pre_process=i) for i in processes)

    def add_post_processes(self, *processes: Process | AsyncProcess):
        self.callbacks.extend(Callback(post_process=i) for i in processes)

    def bind_llm(self, llm: LLM | None):
        self.llm = llm
        return llm

    @property
    def callback(self):
        def wrapper(callback_class: type[Callback]):
            self.callbacks.append(callback_class())
            return callback_class

        return wrapper

    @property
    def pre_process(self):
        def wrapper(process: Process | AsyncProcess):
            self.add_pre_processes(process)
            return process

        return wrapper

    @property
    def post_process(self):
        def wrapper(process: Process | AsyncProcess):
            self.add_post_processes(process)
            return process

        return wrapper

    def _apply_pre_processes(self, context):
        for callback in self.callbacks:
            context |= callback.pre_process(context) or {}

    def _apply_post_processes(self, context):
        for callback in self.callbacks:
            context |= callback.post_process(context) or {}

    def _invoke(self, context, /, complete=None):
        complete = self.llm.complete if self.llm else complete
        assert complete is not None

        prompt = self.render(context)

        context.result = complete(prompt, **self.run_config)

        self._apply_post_processes(context)

    def _stream(self, context, /, generate=None):
        generate = self.llm.generate if self.llm else generate
        assert generate is not None

        prompt = self.render(context)

        context.result = ""
        for delta in generate(prompt, **self.run_config):  # type: ignore
            context.result += delta
            self._apply_post_processes(context)
            yield context

    async def _apply_async_pre_processes(self, context):
        for callback in self.callbacks:
            context |= await resolve(callback.pre_process(context)) or {}

    async def _apply_async_post_processes(self, context):
        for callback in self.callbacks:
            context |= await resolve(callback.post_process(context)) or {}

    async def _ainvoke(self, context, /, complete=None):
        complete = self.llm.complete if self.llm else complete
        assert complete is not None

        prompt = await self.arender(context)

        context.result = await resolve(complete(prompt, **self.run_config))

        await self._apply_async_post_processes(context)

    async def _astream(self, context, /, generate=None):
        generate = self.llm.generate if self.llm else generate
        assert generate is not None

        prompt = await self.arender(context)

        context.result = ""
        async for delta in generate(prompt, **self.run_config):  # type: ignore
            context.result += delta
            await self._apply_async_post_processes(context)
            yield context

    def next(self, chain: AbstractChain):
        if isinstance(chain, Chain):
            return Chain(self, *chain)
        else:
            return Chain(self, chain)

    def __add__(self, chain: AbstractChain):
        return self.next(chain)

    def render(self, context: Context | None = None):
        context = ChainContext(context, self.context)
        self._apply_pre_processes(context)
        return self.template.render(context)

    async def arender(self, context: Context | None = None):
        context = ChainContext(context, self.context)
        await self._apply_async_pre_processes(context)
        return await self.template.arender(context)

    def __str__(self):
        return f"</{self.name}/>"


class Chain(Interruptable):
    def __init__(
        self,
        *nodes: AbstractChain,
        partial_context: Context | None = None,
    ):
        self.nodes = nodes
        self._context = partial_context

    def next(self, chain: AbstractChain):
        if isinstance(chain, Node):
            return Chain(*self, chain)
        elif isinstance(chain, Chain):
            return Chain(*self, *chain)
        else:
            raise NotImplementedError

    def __add__(self, chain):
        return self.next(chain)

    def __iter__(self):
        return iter(self.nodes)

    def _invoke(self, context, /, complete=None):
        for node in self.nodes:
            node.invoke(context, complete)

    async def _ainvoke(self, context, /, complete=None):
        for node in self.nodes:
            await node.ainvoke(context, complete)

    def _stream(self, context, /, generate=None):
        for node in self.nodes:
            yield from node.stream(context, generate)

    async def _astream(self, context, /, generate=None):
        for node in self.nodes:
            async for i in node.astream(context, generate):
                yield i

    def __repr__(self):
        return " + ".join(map(str, self.nodes))


class JumpTo(Exception):
    def __init__(
        self,
        chain: Interruptable,
        context: Context | None = None,
        target: Interruptable | None = None,
    ):
        self.chain = chain
        self.context = context
        self.target = target

    def __str__(self):
        return f"{self.target} does not exist in the hierarchy"
