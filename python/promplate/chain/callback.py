from typing import TYPE_CHECKING, Awaitable, Callable, Protocol

from ..prompt import Context

if TYPE_CHECKING:
    from .node import AsyncProcess, ChainContext, Process


class AbstractCallback(Protocol):
    def pre_process(self, context: "ChainContext") -> Context | Awaitable[Context | None] | None:
        pass

    def post_process(self, context: "ChainContext") -> Context | Awaitable[Context | None] | None:
        pass

    def on_enter(self, context: Context | None, config: Context) -> tuple[Context | None, Context]:
        return context, config

    def on_leave(self, context: "ChainContext", config: Context) -> tuple["ChainContext", Context]:
        return context, config


class Callback(AbstractCallback):
    def __init__(
        self,
        *,
        pre_process: "Process | AsyncProcess | None" = None,
        post_process: "Process | AsyncProcess | None" = None,
        on_enter: Callable[[Context | None, Context], tuple[Context | None, Context]] | None = None,
        on_leave: Callable[["ChainContext", Context], tuple["ChainContext", Context]] | None = None,
    ) -> None:
        self._pre_process = pre_process
        self._post_process = post_process
        self._on_enter = on_enter
        self._on_leave = on_leave

    def pre_process(self, context):
        if self._pre_process is not None:
            return self._pre_process(context)

    def post_process(self, context):
        if self._post_process is not None:
            return self._post_process(context)

    def on_enter(self, context, config):
        if self._on_enter is not None:
            return self._on_enter(context, config)
        return context, config

    def on_leave(self, context, config):
        if self._on_leave is not None:
            return self._on_leave(context, config)
        return context, config
