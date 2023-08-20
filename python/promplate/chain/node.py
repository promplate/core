from inspect import iscoroutinefunction
from typing import Awaitable, Callable

from promplate.llm.base import *
from promplate.prompt import ChatTemplate, Template
from promplate.prompt.template import Context

Process = Callable[[Context], Context]

AsyncProcess = Callable[[Context], Awaitable[Context]]


class Node:
    def __init__(
        self,
        template: Template,
        pre_processes: list[Process | AsyncProcess] | None = None,
        post_processes: list[Process | AsyncProcess] | None = None,
    ):
        self.template = template
        self.pre_processes = pre_processes or []
        self.post_processes = post_processes or []

    def run(self, context: Context, complete: Complete):
        for process in self.pre_processes:
            context = process(context)

        prompt = self.template.render(context)

        assert isinstance(self.template, ChatTemplate) ^ isinstance(prompt, str)

        result = {"__result__": complete(prompt)}

        for process in self.post_processes:
            result = process(result)

        return result

    async def arun(self, context: Context, complete: Complete | AsyncComplete):
        for process in self.pre_processes:
            if iscoroutinefunction(process):
                context = await process(context)
            else:
                context = process(context)

        prompt = await self.template.arender(context)

        assert isinstance(self.template, ChatTemplate) ^ isinstance(prompt, str)

        if iscoroutinefunction(complete):
            result = {"__result__": await complete(prompt)}
        else:
            result = {"__result__": complete(prompt)}

        for process in self.post_processes:
            if iscoroutinefunction(process):
                context = await process(context)
            else:
                context = process(context)

        return result
