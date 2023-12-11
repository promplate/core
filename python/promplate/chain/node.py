from collections import ChainMap
from inspect import isclass
from typing import TYPE_CHECKING, Callable, Mapping, MutableMapping, overload

from ..llm.base import *
from ..llm.base import AsyncGenerate, AsyncIterable, Generate, Iterable
from ..prompt.template import Context, Loader, Template
from .callback import BaseCallback, Callback
from .utils import iterate, resolve


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


Process = Callable[[ChainContext], Context | None]

AsyncProcess = Callable[[ChainContext], Awaitable[Context | None]]


class AbstractChain(Protocol):
    def invoke(
        self,
        context: Context | None = None,
        /,
        complete: Complete | None = None,
        **config,
    ) -> ChainContext:
        ...

    async def ainvoke(
        self,
        context: Context | None = None,
        /,
        complete: Complete | AsyncComplete | None = None,
        **config,
    ) -> ChainContext:
        ...

    def stream(
        self,
        context: Context | None = None,
        /,
        generate: Generate | None = None,
        **config,
    ) -> Iterable[ChainContext]:
        ...

    def astream(
        self,
        context: Context | None = None,
        /,
        generate: Generate | AsyncGenerate | None = None,
        **config,
    ) -> AsyncIterable[ChainContext]:
        ...


def ensure_callbacks(callbacks: list[BaseCallback | type[BaseCallback]]) -> list[BaseCallback]:
    return [i() if isclass(i) else i for i in callbacks]


class Interruptable(AbstractChain, Protocol):
    def _invoke(
        self,
        context: ChainContext,
        /,
        complete: Complete | None,
        callbacks: list[BaseCallback],
        **config,
    ):
        ...

    async def _ainvoke(
        self,
        context: ChainContext,
        /,
        complete: Complete | AsyncComplete | None,
        callbacks: list[BaseCallback],
        **config,
    ):
        ...

    def _stream(
        self,
        context: ChainContext,
        /,
        generate: Generate | None,
        callbacks: list[BaseCallback],
        **config,
    ) -> Iterable:
        ...

    def _astream(
        self,
        context: ChainContext,
        /,
        generate: Generate | AsyncGenerate | None,
        callbacks: list[BaseCallback],
        **config,
    ) -> AsyncIterable:
        ...

    callbacks: list[BaseCallback | type[BaseCallback]]

    def enter(self, context: Context | None, config: Context):
        callbacks: list[BaseCallback] = ensure_callbacks(self.callbacks)
        for callback in callbacks:
            context, config = callback.on_enter(context, config)
        return context, config, callbacks

    def leave(self, context: ChainContext, config: Context, callbacks: list[BaseCallback]):
        for callback in reversed(callbacks):
            context, config = callback.on_leave(context, config)
        return context, config

    def invoke(self, context=None, /, complete=None, **config) -> ChainContext:
        context, config, callbacks = self.enter(context, config)
        context = ChainContext.ensure(context)

        try:
            self._invoke(ChainContext(context, self.context), complete, callbacks, **config)
            context, config = self.leave(context, config, callbacks)
        except JumpTo as jump:
            context, config = self.leave(context, config, callbacks)
            if jump.target is None or jump.target is self:
                jump.chain.invoke(context, complete, **config)
            else:
                raise jump from None

        return context

    async def ainvoke(self, context=None, /, complete=None, **config) -> ChainContext:
        context, config, callbacks = self.enter(context, config)
        context = ChainContext.ensure(context)

        try:
            await self._ainvoke(ChainContext(context, self.context), complete, callbacks, **config)
            context, config = self.leave(context, config, callbacks)
        except JumpTo as jump:
            context, config = self.leave(context, config, callbacks)
            if jump.target is None or jump.target is self:
                await jump.chain.ainvoke(context, complete, **config)
            else:
                raise jump from None

        return context

    def stream(self, context=None, /, generate=None, **config) -> Iterable[ChainContext]:
        context, config, callbacks = self.enter(context, config)
        context = ChainContext.ensure(context)

        try:
            for _ in self._stream(ChainContext(context, self.context), generate, callbacks, **config):
                yield context
            context, config = self.leave(context, config, callbacks)
        except JumpTo as jump:
            context, config = self.leave(context, config, callbacks)
            if jump.target is None or jump.target is self:
                yield from jump.chain.stream(context, generate, **config)
            else:
                raise jump from None

    async def astream(self, context=None, /, generate=None, **config) -> AsyncIterable[ChainContext]:
        context, config, callbacks = self.enter(context, config)
        context = ChainContext.ensure(context)

        try:
            async for _ in self._astream(ChainContext(context, self.context), generate, callbacks, **config):
                yield context
            context, config = self.leave(context, config, callbacks)
        except JumpTo as jump:
            context, config = self.leave(context, config, callbacks)
            if jump.target is None or jump.target is self:
                async for i in jump.chain.astream(context, generate, **config):
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
        self.callbacks: list[BaseCallback | type[BaseCallback]] = []
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
        def wrapper(callback_class: type[BaseCallback]):
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

    @staticmethod
    def _apply_pre_processes(context, callbacks: list[BaseCallback]):
        for callback in callbacks:
            context |= callback.pre_process(context) or {}

    @staticmethod
    def _apply_post_processes(context, callbacks: list[BaseCallback]):
        for callback in callbacks:
            context |= callback.post_process(context) or {}

    def _invoke(self, context, /, complete, callbacks, **config):
        complete = self.llm.complete if self.llm else complete
        assert complete is not None

        prompt = self.render(context)

        context.result = complete(prompt, **self.run_config, **config)

        self._apply_post_processes(context, callbacks)

    def _stream(self, context, /, generate, callbacks, **config):
        generate = self.llm.generate if self.llm else generate
        assert generate is not None

        prompt = self.render(context)

        context.result = ""
        for delta in generate(prompt, **self.run_config, **config):  # type: ignore
            context.result += delta
            self._apply_post_processes(context, callbacks)
            yield context

    @staticmethod
    async def _apply_async_pre_processes(context, callbacks: list[BaseCallback]):
        for callback in callbacks:
            context |= await resolve(callback.pre_process(context)) or {}

    @staticmethod
    async def _apply_async_post_processes(context, callbacks: list[BaseCallback]):
        for callback in callbacks:
            context |= await resolve(callback.post_process(context)) or {}

    async def _ainvoke(self, context, /, complete, callbacks, **config):
        complete = self.llm.complete if self.llm else complete
        assert complete is not None

        prompt = await self.arender(context)

        context.result = await resolve(complete(prompt, **self.run_config, **config))

        await self._apply_async_post_processes(context, callbacks)

    async def _astream(self, context, /, generate, callbacks, **config):
        generate = self.llm.generate if self.llm else generate
        assert generate is not None

        prompt = await self.arender(context)

        context.result = ""
        async for delta in iterate(generate(prompt, **self.run_config, **config)):
            context.result += delta
            await self._apply_async_post_processes(context, callbacks)
            yield context

    @staticmethod
    def _get_chain_type():
        return Chain

    def __add__(self, chain: AbstractChain):
        if isinstance(chain, Chain):
            return self._get_chain_type()(self, *chain)
        else:
            return self._get_chain_type()(self, chain)

    def render(self, context: Context | None = None, callbacks: list[BaseCallback] | None = None):
        if callbacks is None:
            callbacks = ensure_callbacks(self.callbacks)
        context = ChainContext(context, self.context)
        self._apply_pre_processes(context, callbacks)
        return self.template.render(context)

    async def arender(self, context: Context | None = None, callbacks: list[BaseCallback] | None = None):
        if callbacks is None:
            callbacks = ensure_callbacks(self.callbacks)
        context = ChainContext(context, self.context)
        await self._apply_async_pre_processes(context, callbacks)
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
        self.callbacks: list[BaseCallback | type[BaseCallback]] = []

    def next(self, chain: AbstractChain):
        if isinstance(chain, Node):
            return self.__class__(*self, chain)
        elif isinstance(chain, Chain):
            return self.__class__(*self, *chain)
        else:
            raise NotImplementedError

    def __add__(self, chain):
        return self.next(chain)

    def __iter__(self):
        return iter(self.nodes)

    def _invoke(self, context, /, complete, callbacks: list[BaseCallback], **config):
        for node in self.nodes:
            node.invoke(context, complete, **config)

    async def _ainvoke(self, context, /, complete, callbacks: list[BaseCallback], **config):
        for node in self.nodes:
            await node.ainvoke(context, complete, **config)

    def _stream(self, context, /, generate, callbacks: list[BaseCallback], **config):
        for node in self.nodes:
            yield from node.stream(context, generate, **config)

    async def _astream(self, context, /, generate, callbacks: list[BaseCallback], **config):
        for node in self.nodes:
            async for i in node.astream(context, generate, **config):
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
