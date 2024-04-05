from typing import TYPE_CHECKING, Awaitable, Callable, Protocol

from ..prompt import Context

if TYPE_CHECKING:
    from .node import AsyncProcess, ChainContext, Interruptable, Process


class BaseCallback(Protocol):
    def pre_process(self, context: "ChainContext") -> Context | Awaitable[Context | None] | None: ...

    def mid_process(self, context: "ChainContext") -> Context | Awaitable[Context | None] | None: ...

    def end_process(self, context: "ChainContext") -> Context | Awaitable[Context | None] | None: ...

    def on_enter(self, node: "Interruptable", context: Context | None, config: Context) -> tuple[Context | None, Context]:
        return context, config

    def on_leave(self, node: "Interruptable", context: "ChainContext", config: Context) -> tuple["ChainContext", Context]:
        return context, config


class Callback(BaseCallback):
    def __init__(
        self,
        *,
        pre_process: "Process | AsyncProcess | None" = None,
        mid_process: "Process | AsyncProcess | None" = None,
        end_process: "Process | AsyncProcess | None" = None,
        on_enter: Callable[["Interruptable", Context | None, Context], tuple[Context | None, Context]] | None = None,
        on_leave: Callable[["Interruptable", "ChainContext", Context], tuple["ChainContext", Context]] | None = None,
    ):
        self._pre_process = pre_process
        self._mid_process = mid_process
        self._end_process = end_process
        self._on_enter = on_enter
        self._on_leave = on_leave

    def pre_process(self, context):
        if self._pre_process is not None:
            return self._pre_process(context)

    def mid_process(self, context):
        if self._mid_process is not None:
            return self._mid_process(context)

    def end_process(self, context):
        if self._end_process is not None:
            return self._end_process(context)

    def on_enter(self, node, context, config):
        if self._on_enter is not None:
            return self._on_enter(node, context, config)
        return context, config

    def on_leave(self, node, context, config):
        if self._on_leave is not None:
            return self._on_leave(node, context, config)
        return context, config
