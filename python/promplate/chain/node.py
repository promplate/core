from inspect import iscoroutinefunction
from typing import Awaitable, Callable, Protocol

from promplate.llm.base import *
from promplate.prompt import ChatTemplate, Template
from promplate.prompt.template import AutoNaming, Context

from .utils import appender, count_position_parameters

PostProcessReturns = Context | None | tuple[Context | None, str]

PreProcess = Callable[[Context], Context]
PostProcess = (
    Callable[[Context], PostProcessReturns]
    | Callable[[Context, str], PostProcessReturns]
)

AsyncPreProcess = Callable[[Context], Awaitable[Context]]
AsyncPostProcess = (
    Callable[[Context], Awaitable[PostProcessReturns]]
    | Callable[[Context, str], Awaitable[PostProcessReturns]]
)


class AbstractChain(Protocol):
    def run(
        self,
        context: Context,
        complete: Complete | None = None,
    ) -> Context:
        ...

    async def arun(
        self,
        context: Context,
        complete: Complete | AsyncComplete | None = None,
    ) -> Context:
        ...

    complete: Complete | AsyncComplete | None


class Interruptable(AbstractChain, Protocol):
    def _run(
        self,
        context: Context,
        complete: Complete | None = None,
    ) -> Context:
        ...

    async def _arun(
        self,
        context: Context,
        complete: Complete | AsyncComplete | None = None,
    ) -> Context:
        ...

    def run(self, context, complete=None) -> Context:
        complete = complete or self.complete
        try:
            return self._run(context, complete)
        except JumpTo as jump:
            if jump.target is None or jump.target is self:
                return jump.chain.run(jump.context or context, complete)
            else:
                raise jump from None

    async def arun(self, context, complete=None) -> Context:
        complete = complete or self.complete
        try:
            return await self._arun(context, complete)
        except JumpTo as jump:
            if jump.target is None or jump.target is self:
                return await jump.chain.arun(jump.context or context, complete)
            else:
                raise jump from None


class Node(AutoNaming, Interruptable):
    def __init__(
        self,
        template: Template | ChatTemplate,
        pre_processes: list[PreProcess | AsyncPreProcess] | None = None,
        post_processes: list[PostProcess | AsyncPostProcess] | None = None,
        complete: Complete | AsyncComplete | None = None,
        **config,
    ):
        self.template = template
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
    def _via(process: PostProcess | AsyncPostProcess, context: Context, result):
        if count_position_parameters(process) == 1:
            return process(context)
        else:
            return process(context, result)

    def _apply_pre_processes(self, context: Context):
        for process in self.pre_processes:
            context = process(context) or context
        return context

    def _apply_post_processes(self, context: Context, result):
        for process in self.post_processes:
            ret = self._via(process, context, result) or context
            if isinstance(ret, tuple):
                ret, result = ret
            context = ret or context

        return context

    def _run(self, context, complete=None):
        complete = complete or self.complete
        assert complete is not None

        context = self._apply_pre_processes(context)
        prompt = self.template.render(context)

        assert isinstance(self.template, ChatTemplate) ^ isinstance(prompt, str)

        result = context["__result__"] = complete(prompt, **self.run_config)

        context = self._apply_post_processes(context, result)

        return context

    async def _apply_async_pre_processes(self, context: Context):
        for process in self.pre_processes:
            if iscoroutinefunction(process):
                context = await process(context) or context
            else:
                context = process(context) or context

        return context

    async def _apply_async_post_processes(self, context: Context, result):
        for process in self.post_processes:
            if iscoroutinefunction(process):
                ret = await self._via(process, context, result)
            else:
                ret = self._via(process, context, result)

            if isinstance(ret, tuple):
                ret, result = ret
            context = ret or context

        return context

    async def _arun(self, context, complete=None):
        complete = complete or self.complete
        assert complete is not None

        context = await self._apply_async_pre_processes(context)
        prompt = await self.template.arender(context)

        assert isinstance(self.template, ChatTemplate) ^ isinstance(prompt, str)

        if iscoroutinefunction(complete):
            result = context["__result__"] = await complete(prompt, **self.run_config)
        else:
            result = context["__result__"] = complete(prompt, **self.run_config)

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
        context = self._apply_pre_processes(context)
        return self.template.render(context)

    async def arender(self, context: Context):
        context = await self._apply_async_pre_processes(context)
        return await self.template.arender(context)

    def __str__(self):
        return f"</{self.name}/>"


class Chain(Interruptable):
    def __init__(
        self,
        *nodes: AbstractChain,
        complete: Complete | AsyncComplete | None = None,
    ):
        self.nodes = list(nodes)
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

    def _run(self, context, complete=None):
        for node in self.nodes:
            context = node.run(context, node.complete or complete)

        return context

    async def _arun(self, context, complete=None):
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
