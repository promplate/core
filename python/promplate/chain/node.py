from collections import ChainMap
from typing import Callable, Mapping, MutableMapping, TypeVar, overload

from ..llm.base import *
from ..prompt.template import Context, Loader, Template
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


CTX = TypeVar("CTX", Context, ChainContext)


Process = Callable[[CTX], CTX | None]

AsyncProcess = Callable[[CTX], Awaitable[CTX | None]]


class AbstractChain(Protocol):
    def run(
        self,
        context: Context | None = None,
        /,
        complete: Complete | None = None,
    ) -> ChainContext:
        ...

    async def arun(
        self,
        context: Context | None = None,
        /,
        complete: Complete | AsyncComplete | None = None,
    ) -> ChainContext:
        ...

    context: Context

    complete: Complete | AsyncComplete | None


class Interruptable(AbstractChain, Protocol):
    def _run(
        self,
        context: ChainContext,
        /,
        complete: Complete | None = None,
    ) -> ChainContext:
        ...

    async def _arun(
        self,
        context: ChainContext,
        /,
        complete: Complete | AsyncComplete | None = None,
    ) -> ChainContext:
        ...

    def run(self, context=None, /, complete=None) -> ChainContext:
        context = ChainContext.ensure(context)

        try:
            self._run(ChainContext(context, self.context), complete)
        except JumpTo as jump:
            if jump.target is None or jump.target is self:
                jump.chain.run(context, complete)
            else:
                raise jump from None

        return context

    async def arun(self, context=None, /, complete=None) -> ChainContext:
        context = ChainContext.ensure(context)

        try:
            await self._arun(ChainContext(context, self.context), complete)
        except JumpTo as jump:
            if jump.target is None or jump.target is self:
                await jump.chain.arun(context, complete)
            else:
                raise jump from None

        return context

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
        pre_processes: list[Process | AsyncProcess] | None = None,
        post_processes: list[Process | AsyncProcess] | None = None,
        complete: Complete | AsyncComplete | None = None,
        **config,
    ):
        self.template = Template(template) if isinstance(template, str) else template
        self._context = partial_context
        self.pre_processes = pre_processes or []
        self.post_processes = post_processes or []
        self.complete = complete
        self.run_config = config

    @property
    def pre_process(self):
        return appender(self.pre_processes)

    @property
    def post_process(self):
        return appender(self.post_processes)

    def _apply_pre_processes(self, context):
        for process in self.pre_processes:
            context |= process(context)

    def _apply_post_processes(self, context):
        for process in self.post_processes:
            context |= process(context)

    def _run(self, context, /, complete=None):
        complete = self.complete or complete
        assert complete is not None

        self._apply_pre_processes(context)
        prompt = self.template.render(context)

        context.result = complete(prompt, **self.run_config)

        self._apply_post_processes(context)

    async def _apply_async_pre_processes(self, context):
        for process in self.pre_processes:
            context |= await resolve(process(context))

    async def _apply_async_post_processes(self, context):
        for process in self.post_processes:
            context |= await resolve(process(context))

    async def _arun(self, context, /, complete=None):
        complete = self.complete or complete
        assert complete is not None

        await self._apply_async_pre_processes(context)
        prompt = await self.template.arender(context)

        context.result = await resolve(complete(prompt, **self.run_config))

        await self._apply_async_post_processes(context)

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
        complete: Complete | AsyncComplete | None = None,
    ):
        self.nodes = nodes
        self._context = partial_context
        self.complete = complete

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

    def _run(self, context, /, complete=None):
        for node in self.nodes:
            context = node.run(context, self.complete or complete)  # type: ignore

        return context

    async def _arun(self, context, /, complete=None):
        for node in self.nodes:
            context = await node.arun(context, self.complete or complete)

        return context

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

    def __str__(self) -> str:
        return f"{self.target} does not exist in the hierarchy"
