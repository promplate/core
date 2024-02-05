from inspect import isclass
from itertools import accumulate
from typing import Callable, Mapping, MutableMapping, overload

from ..llm.base import LLM, AsyncComplete, AsyncGenerate, Complete, Generate
from ..prompt.template import Context, Loader, SafeChainMapContext, Template
from ..typing import AsyncIterable, Awaitable, Callable, Iterable, List, Mapping, MutableMapping, Optional, Protocol, Type, Union, cast, overload
from .callback import BaseCallback, Callback
from .utils import accumulate_any, resolve


class ChainContext(SafeChainMapContext):
    @overload
    def __init__(self): ...

    @overload
    def __init__(self, least: Optional[MutableMapping] = None): ...

    @overload
    def __init__(self, least: Optional[MutableMapping] = None, *maps: Mapping): ...

    def __init__(self, least: Optional[MutableMapping] = None, *maps: Mapping):
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


Process = Callable[[ChainContext], Optional[Context]]

AsyncProcess = Callable[[ChainContext], Awaitable[Optional[Context]]]


class AbstractNode(Protocol):
    def invoke(
        self,
        context: Optional[Context] = None,
        /,
        complete: Optional[Complete] = None,
        **config,
    ) -> ChainContext: ...

    async def ainvoke(
        self,
        context: Optional[Context] = None,
        /,
        complete: Union[Complete, Optional[AsyncComplete]] = None,
        **config,
    ) -> ChainContext: ...

    def stream(
        self,
        context: Optional[Context] = None,
        /,
        generate: Optional[Generate] = None,
        **config,
    ) -> Iterable[ChainContext]: ...

    def astream(
        self,
        context: Optional[Context] = None,
        /,
        generate: Union[Generate, Optional[AsyncGenerate]] = None,
        **config,
    ) -> AsyncIterable[ChainContext]: ...

    @classmethod
    def _get_chain_type(cls):
        return Chain

    def __add__(self, chain: "AbstractNode"):
        if isinstance(chain, Chain):
            return self._get_chain_type()(self, *chain)
        return self._get_chain_type()(self, chain)


def ensure_callbacks(callbacks: List[Union[BaseCallback, Type[BaseCallback]]]) -> List[BaseCallback]:
    return [i() if isclass(i) else i for i in callbacks]


class Interruptable(AbstractNode, Protocol):
    def _invoke(
        self,
        context: ChainContext,
        /,
        complete: Optional[Complete],
        callbacks: List[BaseCallback],
        **config,
    ): ...

    async def _ainvoke(
        self,
        context: ChainContext,
        /,
        complete: Union[Complete, Optional[AsyncComplete]],
        callbacks: List[BaseCallback],
        **config,
    ): ...

    def _stream(
        self,
        context: ChainContext,
        /,
        generate: Optional[Generate],
        callbacks: List[BaseCallback],
        **config,
    ) -> Iterable: ...

    def _astream(
        self,
        context: ChainContext,
        /,
        generate: Union[Generate, Optional[AsyncGenerate]],
        callbacks: List[BaseCallback],
        **config,
    ) -> AsyncIterable: ...

    callbacks: List[Union[BaseCallback, Type[BaseCallback]]]

    def enter(self, context: Optional[Context], config: Context):
        callbacks: List[BaseCallback] = ensure_callbacks(self.callbacks)
        for callback in callbacks:
            context, config = callback.on_enter(self, context, config)
        return context, config, callbacks

    def leave(self, context: ChainContext, config: Context, callbacks: List[BaseCallback]):
        for callback in reversed(callbacks):
            context, config = callback.on_leave(self, context, config)
        return context, config

    def add_pre_processes(self, *processes: Union[Process, AsyncProcess]):
        self.callbacks.extend(Callback(pre_process=i) for i in processes)
        return self

    def add_mid_processes(self, *processes: Union[Process, AsyncProcess]):
        self.callbacks.extend(Callback(mid_process=i) for i in processes)
        return self

    def add_end_processes(self, *processes: Union[Process, AsyncProcess]):
        self.callbacks.extend(Callback(end_process=i) for i in processes)
        return self

    def add_callbacks(self, *callbacks: Union[BaseCallback, Type[BaseCallback]]):
        self.callbacks.extend(callbacks)
        return self

    def pre_process(self, process: Union[Process, AsyncProcess]):
        self.add_pre_processes(process)
        return process

    def mid_process(self, process: Union[Process, AsyncProcess]):
        self.add_mid_processes(process)
        return process

    def end_process(self, process: Union[Process, AsyncProcess]):
        self.add_end_processes(process)
        return process

    def callback(self, callback: Union[BaseCallback, Type[BaseCallback]]):
        self.add_callbacks(callback)
        return callback

    @staticmethod
    def _apply_pre_processes(context: ChainContext, callbacks: List[BaseCallback]):
        for callback in callbacks:
            context.update(cast(Context, callback.pre_process(context) or {}))

    @staticmethod
    def _apply_mid_processes(context: ChainContext, callbacks: List[BaseCallback]):
        for callback in callbacks:
            context.update(cast(Context, callback.mid_process(context) or {}))

    @staticmethod
    def _apply_end_processes(context: ChainContext, callbacks: List[BaseCallback]):
        for callback in reversed(callbacks):
            context.update(cast(Context, callback.end_process(context) or {}))

    @staticmethod
    async def _apply_async_pre_processes(context: ChainContext, callbacks: List[BaseCallback]):
        for callback in callbacks:
            context.update(cast(Context, await resolve(callback.pre_process(context)) or {}))

    @staticmethod
    async def _apply_async_mid_processes(context: ChainContext, callbacks: List[BaseCallback]):
        for callback in callbacks:
            context.update(cast(Context, await resolve(callback.mid_process(context)) or {}))

    @staticmethod
    async def _apply_async_end_processes(context: ChainContext, callbacks: List[BaseCallback]):
        for callback in reversed(callbacks):
            context.update(cast(Context, await resolve(callback.end_process(context)) or {}))

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

    _context: Optional[Context]

    @property
    def context(self):
        if self._context is None:
            self._context = {}
        return self._context

    @context.setter
    def context(self, context: Optional[Context]):
        self._context = context

    @context.deleter
    def context(self):
        self._context = None


class Node(Loader, Interruptable):
    def __init__(
        self,
        template: Union[Template, str],
        partial_context: Optional[Context] = None,
        llm: Optional[LLM] = None,
        **config,
    ):
        self.template = Template(template) if isinstance(template, str) else template
        self._context = partial_context
        self.callbacks: List[Union[BaseCallback, Type[BaseCallback]]] = []
        self.llm = llm
        self.run_config = config

    def _invoke(self, context, /, complete, callbacks, **config):
        complete = cast(Complete, self.llm.complete if self.llm else complete)
        assert complete is not None

        prompt = self.render(context, callbacks)

        context.result = complete(prompt, **({**self.run_config, **config}))

        self._apply_mid_processes(context, callbacks)

        self._apply_end_processes(context, callbacks)

    def _stream(self, context, /, generate, callbacks, **config):
        generate = cast(Generate, self.llm.generate if self.llm else generate)
        assert generate is not None

        prompt = self.render(context, callbacks)

        for result in accumulate(generate(prompt, **({**self.run_config, **config}))):
            context.result = result
            self._apply_mid_processes(context, callbacks)
            yield

        self._apply_end_processes(context, callbacks)

    async def _ainvoke(self, context, /, complete, callbacks, **config):
        complete = cast(Union[Complete, AsyncComplete], self.llm.complete if self.llm else complete)
        assert complete is not None

        prompt = await self.arender(context, callbacks)

        context.result = await resolve(complete(prompt, **({**self.run_config, **config})))

        await self._apply_async_mid_processes(context, callbacks)

        await self._apply_async_end_processes(context, callbacks)

    async def _astream(self, context, /, generate, callbacks, **config):
        generate = cast(Union[Generate, AsyncGenerate], self.llm.generate if self.llm else generate)
        assert generate is not None

        prompt = await self.arender(context, callbacks)

        async for result in accumulate_any(generate(prompt, **({**self.run_config, **config}))):
            context.result = result
            await self._apply_async_mid_processes(context, callbacks)
            yield

        await self._apply_async_end_processes(context, callbacks)

    def render(self, context: Optional[Context] = None, callbacks: Optional[List[BaseCallback]] = None):
        if callbacks is None:
            callbacks = ensure_callbacks(self.callbacks)
        context = ChainContext(context, self.context)
        self._apply_pre_processes(context, callbacks)
        return self.template.render(context)

    async def arender(self, context: Optional[Context] = None, callbacks: Optional[List[BaseCallback]] = None):
        if callbacks is None:
            callbacks = ensure_callbacks(self.callbacks)
        context = ChainContext(context, self.context)
        await self._apply_async_pre_processes(context, callbacks)
        return await self.template.arender(context)

    def __str__(self):
        return f"</{self.name}/>"


class Loop(Interruptable):
    def __init__(self, chain: AbstractNode, partial_context: Optional[Context] = None):
        self.chain = chain
        self._context = partial_context
        self.callbacks: List[Union[BaseCallback, Type[BaseCallback]]] = []

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
    def __init__(self, *nodes: AbstractNode, partial_context: Optional[Context] = None):
        self.nodes = list(nodes)
        self._context = partial_context
        self.callbacks: List[Union[BaseCallback, Type[BaseCallback]]] = []

    @classmethod
    def _get_chain_type(cls):
        return cls

    def __iadd__(self, chain: AbstractNode):
        self.nodes.append(chain)
        return self

    def __iter__(self):
        return iter(self.nodes)

    def _invoke(self, context, /, complete, callbacks: List[BaseCallback], **config):
        self._apply_pre_processes(context, callbacks)
        for node in self.nodes:
            node.invoke(context, complete, **config)
            self._apply_mid_processes(context, callbacks)
        self._apply_end_processes(context, callbacks)

    async def _ainvoke(self, context, /, complete, callbacks: List[BaseCallback], **config):
        await self._apply_async_pre_processes(context, callbacks)
        for node in self.nodes:
            await node.ainvoke(context, complete, **config)
            await self._apply_async_mid_processes(context, callbacks)
        await self._apply_async_end_processes(context, callbacks)

    def _stream(self, context, /, generate, callbacks: List[BaseCallback], **config):
        self._apply_pre_processes(context, callbacks)
        for node in self.nodes:
            for _ in node.stream(context, generate, **config):
                self._apply_mid_processes(context, callbacks)
                yield
        self._apply_end_processes(context, callbacks)

    async def _astream(self, context, /, generate, callbacks: List[BaseCallback], **config):
        await self._apply_async_pre_processes(context, callbacks)
        for node in self.nodes:
            async for _ in node.astream(context, generate, **config):
                await self._apply_async_mid_processes(context, callbacks)
                yield
        await self._apply_async_end_processes(context, callbacks)

    def __repr__(self):
        return " + ".join(map(str, self.nodes))


class Jump(Exception):
    def __init__(self, into: Optional[Interruptable] = None, out_of: Optional[Interruptable] = None):
        self.into = into
        self.out_of = out_of

    def __str__(self):
        return f"{self.out_of} does not exist in the chain hierarchy"
