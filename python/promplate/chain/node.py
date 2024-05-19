from inspect import isclass
from itertools import accumulate
from typing import Callable, Mapping, MutableMapping, TypeVar, overload

from ..llm.base import *
from ..prompt.template import Context, Loader, SafeChainMapContext, Template
from .callback import BaseCallback, Callback
from .utils import accumulate_any, resolve

C = TypeVar("C", bound="ChainContext")


class ChainContext(SafeChainMapContext):
    @overload
    def __new__(cls): ...

    @overload
    def __new__(cls, least: C, *maps: Mapping) -> C: ...

    @overload
    def __new__(cls, least: MutableMapping | None = None, *maps: Mapping): ...

    def __init__(self, least: MutableMapping | None = None, *maps: Mapping):
        super().__init__({} if least is None else least, *maps)  # type: ignore

    def __new__(cls, *args, **kwargs):  # type: ignore
        try:
            least = args[0]
        except IndexError:
            least = kwargs.get("least")
        if isinstance(least, cls) and least.__class__ is not cls:
            return least.__class__(*args, **kwargs)

        return super().__new__(cls, *args, **kwargs)

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

    def __str__(self):
        return str({**self})


Process = Callable[[ChainContext], Context | None]

AsyncProcess = Callable[[ChainContext], Awaitable[Context | None]]


class AbstractNode(Protocol):
    def invoke(
        self,
        context: Context | None = None,
        /,
        complete: Complete | None = None,
        **config,
    ) -> ChainContext: ...

    async def ainvoke(
        self,
        context: Context | None = None,
        /,
        complete: Complete | AsyncComplete | None = None,
        **config,
    ) -> ChainContext: ...

    def stream(
        self,
        context: Context | None = None,
        /,
        generate: Generate | None = None,
        **config,
    ) -> Iterable[ChainContext]: ...

    def astream(
        self,
        context: Context | None = None,
        /,
        generate: Generate | AsyncGenerate | None = None,
        **config,
    ) -> AsyncIterable[ChainContext]: ...

    @classmethod
    def _get_chain_type(cls):
        return Chain

    def __add__(self, chain: "AbstractNode"):
        if isinstance(chain, Chain):
            return self._get_chain_type()(self, *chain)
        return self._get_chain_type()(self, chain)


def ensure_callbacks(callbacks: list[BaseCallback | type[BaseCallback]]) -> list[BaseCallback]:
    return [i() if isclass(i) else i for i in callbacks]


class Interruptable(AbstractNode, Protocol):
    def _invoke(
        self,
        context: ChainContext,
        /,
        complete: Complete | None,
        callbacks: list[BaseCallback],
        **config,
    ): ...

    async def _ainvoke(
        self,
        context: ChainContext,
        /,
        complete: Complete | AsyncComplete | None,
        callbacks: list[BaseCallback],
        **config,
    ): ...

    def _stream(
        self,
        context: ChainContext,
        /,
        generate: Generate | None,
        callbacks: list[BaseCallback],
        **config,
    ) -> Iterable: ...

    def _astream(
        self,
        context: ChainContext,
        /,
        generate: Generate | AsyncGenerate | None,
        callbacks: list[BaseCallback],
        **config,
    ) -> AsyncIterable: ...

    callbacks: list[BaseCallback | type[BaseCallback]]

    def enter(self, context: Context | None, config: Context):
        callbacks: list[BaseCallback] = ensure_callbacks(self.callbacks)
        for callback in callbacks:
            context, config = callback.on_enter(self, context, config)
        return context, config, callbacks

    def leave(self, context: ChainContext, config: Context, callbacks: list[BaseCallback]):
        for callback in reversed(callbacks):
            context, config = callback.on_leave(self, context, config)
        return context, config

    def add_pre_processes(self, *processes: Process | AsyncProcess):
        self.callbacks.extend(Callback(pre_process=i) for i in processes)
        return self

    def add_mid_processes(self, *processes: Process | AsyncProcess):
        self.callbacks.extend(Callback(mid_process=i) for i in processes)
        return self

    def add_end_processes(self, *processes: Process | AsyncProcess):
        self.callbacks.extend(Callback(end_process=i) for i in processes)
        return self

    def add_callbacks(self, *callbacks: BaseCallback | type[BaseCallback]):
        self.callbacks.extend(callbacks)
        return self

    def pre_process(self, process: Process | AsyncProcess):
        self.add_pre_processes(process)
        return process

    def mid_process(self, process: Process | AsyncProcess):
        self.add_mid_processes(process)
        return process

    def end_process(self, process: Process | AsyncProcess):
        self.add_end_processes(process)
        return process

    def callback(self, callback: BaseCallback | type[BaseCallback]):
        self.add_callbacks(callback)
        return callback

    @staticmethod
    def _apply_pre_processes(context: ChainContext, callbacks: list[BaseCallback]):
        for callback in callbacks:
            context |= cast(Context, callback.pre_process(context) or {})

    @staticmethod
    def _apply_mid_processes(context: ChainContext, callbacks: list[BaseCallback]):
        for callback in callbacks:
            context |= cast(Context, callback.mid_process(context) or {})

    @staticmethod
    def _apply_end_processes(context: ChainContext, callbacks: list[BaseCallback]):
        for callback in reversed(callbacks):
            context |= cast(Context, callback.end_process(context) or {})

    @staticmethod
    async def _apply_async_pre_processes(context: ChainContext, callbacks: list[BaseCallback]):
        for callback in callbacks:
            context |= cast(Context, await resolve(callback.pre_process(context)) or {})

    @staticmethod
    async def _apply_async_mid_processes(context: ChainContext, callbacks: list[BaseCallback]):
        for callback in callbacks:
            context |= cast(Context, await resolve(callback.mid_process(context)) or {})

    @staticmethod
    async def _apply_async_end_processes(context: ChainContext, callbacks: list[BaseCallback]):
        for callback in reversed(callbacks):
            context |= cast(Context, await resolve(callback.end_process(context)) or {})

    def invoke(self, context=None, /, complete=None, **config) -> ChainContext:
        context, config, callbacks = self.enter(context, config)
        context = ChainContext.ensure(context)

        try:
            self._invoke(ChainContext(context, self.context), complete, callbacks, **config)
        except Jump as jump:
            context, config = self.leave(context, config, callbacks)
            if jump.out_of is not None and jump.out_of is not self:
                raise jump from None
            if jump.into is not None:
                jump.into.invoke(context, complete, **config)
        else:
            context, config = self.leave(context, config, callbacks)

        return context

    async def ainvoke(self, context=None, /, complete=None, **config) -> ChainContext:
        context, config, callbacks = self.enter(context, config)
        context = ChainContext.ensure(context)

        try:
            await self._ainvoke(ChainContext(context, self.context), complete, callbacks, **config)
        except Jump as jump:
            context, config = self.leave(context, config, callbacks)
            if jump.out_of is not None and jump.out_of is not self:
                raise jump from None
            if jump.into is not None:
                await jump.into.ainvoke(context, complete, **config)
        else:
            context, config = self.leave(context, config, callbacks)

        return context

    def stream(self, context=None, /, generate=None, **config) -> Iterable[ChainContext]:
        context, config, callbacks = self.enter(context, config)
        context = ChainContext.ensure(context)

        try:
            for _ in self._stream(ChainContext(context, self.context), generate, callbacks, **config):
                yield context
        except Jump as jump:
            context, config = self.leave(context, config, callbacks)
            if jump.out_of is not None and jump.out_of is not self:
                raise jump from None
            if jump.into is not None:
                yield from jump.into.stream(context, generate, **config)
        else:
            context, config = self.leave(context, config, callbacks)

    async def astream(self, context=None, /, generate=None, **config) -> AsyncIterable[ChainContext]:
        context, config, callbacks = self.enter(context, config)
        context = ChainContext.ensure(context)

        try:
            async for _ in self._astream(ChainContext(context, self.context), generate, callbacks, **config):
                yield context
        except Jump as jump:
            context, config = self.leave(context, config, callbacks)
            if jump.out_of is not None and jump.out_of is not self:
                raise jump from None
            if jump.into is not None:
                async for i in jump.into.astream(context, generate, **config):
                    yield i
        else:
            context, config = self.leave(context, config, callbacks)

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

    def _invoke(self, context, /, complete, callbacks, **config):
        complete = cast(Complete, self.llm.complete if self.llm else complete)
        assert complete is not None

        prompt = self.render(context, callbacks)

        context.result = complete(prompt, **(self.run_config | config))

        self._apply_mid_processes(context, callbacks)

        self._apply_end_processes(context, callbacks)

    def _stream(self, context, /, generate, callbacks, **config):
        generate = cast(Generate, self.llm.generate if self.llm else generate)
        assert generate is not None

        prompt = self.render(context, callbacks)

        for result in accumulate(generate(prompt, **(self.run_config | config))):
            context.result = result
            self._apply_mid_processes(context, callbacks)
            yield

        self._apply_end_processes(context, callbacks)

    async def _ainvoke(self, context, /, complete, callbacks, **config):
        complete = cast(Complete | AsyncComplete, self.llm.complete if self.llm else complete)
        assert complete is not None

        prompt = await self.arender(context, callbacks)

        context.result = await resolve(complete(prompt, **(self.run_config | config)))

        await self._apply_async_mid_processes(context, callbacks)

        await self._apply_async_end_processes(context, callbacks)

    async def _astream(self, context, /, generate, callbacks, **config):
        generate = cast(Generate | AsyncGenerate, self.llm.generate if self.llm else generate)
        assert generate is not None

        prompt = await self.arender(context, callbacks)

        async for result in accumulate_any(generate(prompt, **(self.run_config | config))):
            context.result = result
            await self._apply_async_mid_processes(context, callbacks)
            yield

        await self._apply_async_end_processes(context, callbacks)

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


class Loop(Interruptable):
    def __init__(self, chain: AbstractNode, partial_context: Context | None = None):
        self.chain = chain
        self._context = partial_context
        self.callbacks: list[BaseCallback | type[BaseCallback]] = []

    def _invoke(self, context, /, complete, callbacks, **config):
        while True:
            self._apply_pre_processes(context, callbacks)
            self.chain.invoke(context, complete, **config)
            self._apply_mid_processes(context, callbacks)
            self._apply_end_processes(context, callbacks)

    async def _ainvoke(self, context, /, complete, callbacks, **config):
        while True:
            await self._apply_async_pre_processes(context, callbacks)
            await self.chain.ainvoke(context, complete, **config)
            await self._apply_async_mid_processes(context, callbacks)
            await self._apply_async_end_processes(context, callbacks)

    def _stream(self, context, /, generate, callbacks, **config):
        while True:
            self._apply_pre_processes(context, callbacks)
            for _ in self.chain.stream(context, generate, **config):
                self._apply_mid_processes(context, callbacks)
                yield
            self._apply_end_processes(context, callbacks)

    async def _astream(self, context, /, generate, callbacks, **config):
        while True:
            await self._apply_async_pre_processes(context, callbacks)
            async for _ in self.chain.astream(context, generate, **config):
                await self._apply_async_mid_processes(context, callbacks)
                yield
            await self._apply_async_end_processes(context, callbacks)


class Chain(Interruptable):
    def __init__(self, *nodes: AbstractNode, partial_context: Context | None = None):
        self.nodes = list(nodes)
        self._context = partial_context
        self.callbacks: list[BaseCallback | type[BaseCallback]] = []

    @classmethod
    def _get_chain_type(cls):
        return cls

    def __iadd__(self, chain: AbstractNode):
        self.nodes.append(chain)
        return self

    def __iter__(self):
        return iter(self.nodes)

    def _invoke(self, context, /, complete, callbacks: list[BaseCallback], **config):
        self._apply_pre_processes(context, callbacks)
        for node in self.nodes:
            node.invoke(context, complete, **config)
            self._apply_mid_processes(context, callbacks)
        self._apply_end_processes(context, callbacks)

    async def _ainvoke(self, context, /, complete, callbacks: list[BaseCallback], **config):
        await self._apply_async_pre_processes(context, callbacks)
        for node in self.nodes:
            await node.ainvoke(context, complete, **config)
            await self._apply_async_mid_processes(context, callbacks)
        await self._apply_async_end_processes(context, callbacks)

    def _stream(self, context, /, generate, callbacks: list[BaseCallback], **config):
        self._apply_pre_processes(context, callbacks)
        for node in self.nodes:
            for _ in node.stream(context, generate, **config):
                self._apply_mid_processes(context, callbacks)
                yield
        self._apply_end_processes(context, callbacks)

    async def _astream(self, context, /, generate, callbacks: list[BaseCallback], **config):
        await self._apply_async_pre_processes(context, callbacks)
        for node in self.nodes:
            async for _ in node.astream(context, generate, **config):
                await self._apply_async_mid_processes(context, callbacks)
                yield
        await self._apply_async_end_processes(context, callbacks)

    def __repr__(self):
        return " + ".join(map(str, self.nodes))


class Jump(Exception):
    def __init__(self, into: Interruptable | None = None, out_of: Interruptable | None = None):
        self.into = into
        self.out_of = out_of

    def __str__(self):
        return f"{self.out_of} does not exist in the chain hierarchy"
