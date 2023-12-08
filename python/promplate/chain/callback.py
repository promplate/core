from typing import TYPE_CHECKING, Awaitable, Protocol

from ..prompt import Context

if TYPE_CHECKING:
    from .node import AsyncProcess, ChainContext, Process


class AbstractCallback(Protocol):
    def pre_process(self, context: "ChainContext") -> Context | Awaitable[Context | None] | None:
        ...

    def post_process(self, context: "ChainContext") -> Context | Awaitable[Context | None] | None:
        ...


class Callback(AbstractCallback):
    def __init__(
        self,
        *,
        pre_process: "Process | AsyncProcess | None" = None,
        post_process: "Process | AsyncProcess | None" = None,
    ) -> None:
        self._pre_process = pre_process
        self._post_process = post_process

    def pre_process(self, context):
        if self._pre_process is not None:
            return self._pre_process(context)

    def post_process(self, context):
        if self._post_process is not None:
            return self._post_process(context)
