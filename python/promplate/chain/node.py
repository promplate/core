from collections import ChainMap
from typing import Any, Callable, Mapping, MutableMapping, Self, TypeVar

from ..llm.base import *
from ..prompt.template import Context, Loader, Template
from .utils import appender, count_position_parameters, resolve


class ChainContext(ChainMap, dict):
    def __init__(self, *maps: MutableMapping[Any, Any] | None):
        super().__init__(*(m for m in maps if m is not None))

    @property
    def result(self):
        return self.__getitem__("__result__")

    def __or__(self, other: Mapping | None) -> Self:
        return self if other is None or other is self else super().__or__(other)


CTX = TypeVar("CTX", Context, ChainContext)

PostProcessReturns = CTX | None | tuple[CTX | None, str]

PreProcess = Callable[[CTX], CTX]
PostProcess = (
    Callable[[CTX], PostProcessReturns] | Callable[[CTX, str], PostProcessReturns]
)

AsyncPreProcess = Callable[[CTX], Awaitable[CTX]]
AsyncPostProcess = (
    Callable[[CTX], Awaitable[PostProcessReturns]]
    | Callable[[CTX, str], Awaitable[PostProcessReturns]]
)


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

    partial_context: Context | None

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

    def run(self, context=None, /, complete=None):
        context = ChainContext(self.partial_context, context)
        complete = complete or self.complete
        try:
            return self._run(context, complete)
        except JumpTo as jump:
            if jump.target is None or jump.target is self:
                return jump.chain.run(context | jump.context, complete)
            else:
                raise jump from None

    async def arun(self, context=None, /, complete=None):
        context = ChainContext(self.partial_context, context)
        complete = complete or self.complete
        try:
            return await self._arun(context, complete)
        except JumpTo as jump:
            if jump.target is None or jump.target is self:
                return await jump.chain.arun(context | jump.context, complete)
            else:
                raise jump from None


class Node(Loader, Interruptable):
    def __init__(
        self,
        template: Template | str,
        partial_context: Context | None = None,
        pre_processes: list[PreProcess | AsyncPreProcess] | None = None,
        post_processes: list[PostProcess | AsyncPostProcess] | None = None,
        complete: Complete | AsyncComplete | None = None,
        **config,
    ):
        self.template = Template(template) if isinstance(template, str) else template
        self.partial_context = partial_context
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

    @staticmethod
    def _via(process: PostProcess | AsyncPostProcess, context: ChainContext, result):
        if count_position_parameters(process) == 1:
            return process(context)
        else:
            return process(context, result)

    def _apply_pre_processes(self, context: CTX) -> CTX:
        for process in self.pre_processes:
            context |= process(context)
        return context

    def _apply_post_processes(self, context: CTX, result) -> CTX:
        for process in self.post_processes:
            ret = self._via(process, context, result)
            if isinstance(ret, tuple):
                ret, result = ret
            context |= ret
        return context

    def _run(self, context, /, complete=None):
        complete = complete or self.complete
        assert complete is not None

        context = self._apply_pre_processes(context)
        prompt = self.template.render(context)

        result = context["__result__"] = complete(prompt, **self.run_config)

        context = self._apply_post_processes(context, result)

        return context

    async def _apply_async_pre_processes(self, context: CTX) -> CTX:
        for process in self.pre_processes:
            context |= await resolve(process(context))
        return context

    async def _apply_async_post_processes(self, context: CTX, result) -> CTX:
        for process in self.post_processes:
            ret = await resolve(self._via(process, context, result))
            if isinstance(ret, tuple):
                ret, result = ret
            context |= ret
        return context

    async def _arun(self, context, /, complete=None):
        complete = complete or self.complete
        assert complete is not None
        context = ChainContext(context, self.partial_context)

        context = await self._apply_async_pre_processes(context)
        prompt = await self.template.arender(context)

        result = context["__result__"] = await resolve(
            complete(prompt, **self.run_config)
        )

        context = await self._apply_async_post_processes(context, result)

        return context

    def next(self, chain: AbstractChain):
        if isinstance(chain, Chain):
            return Chain(self, *chain)
        else:
            return Chain(self, chain)

    def __add__(self, chain: AbstractChain):
        return self.next(chain)

    def render(self, context: Context):
        context = ChainContext(context, self.partial_context)
        context = self._apply_pre_processes(context)
        return self.template.render(context)

    async def arender(self, context: Context):
        context = ChainContext(context, self.partial_context)
        context = await self._apply_async_pre_processes(context)
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
        self.nodes = list(nodes)
        self.partial_context = partial_context
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
            context = node.run(context, node.complete or complete)

        return context

    async def _arun(self, context, /, complete=None):
        for node in self.nodes:
            context = await node.arun(context, node.complete or complete)

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
