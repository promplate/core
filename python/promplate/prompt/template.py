from copy import copy
from functools import cached_property
from pathlib import Path
from typing import Any, Protocol

from .builder import *
from .utils import *

Context = dict[str, Any]  # globals must be a real dict


class Component(Protocol):
    def render(self, context: Context) -> str:
        ...

    async def arender(self, context: Context) -> str:
        ...


class TemplateCore(AutoNaming):
    """A simple template compiler, for a jinja2-like syntax."""

    def __init__(self, text: str):
        """Construct a Templite with the given `text`."""

        self.text = text
        self._buffer = []
        self._ops_stack = []

    def _flush(self):
        for line in self._buffer:
            self._builder.add_line(line)
        self._buffer.clear()

    @staticmethod
    def _unwrap_token(token: str):
        return token.strip()[2:-2].strip("-").strip()

    def _on_literal_token(self, token: str):
        self._buffer.append(f"append_result({repr(token)})")

    def _on_eval_token(self, token):
        exp = self._unwrap_token(token)
        self._buffer.append(f"append_result({exp})")

    def _on_exec_token(self, token):
        exp = self._unwrap_token(token)
        self._buffer.append(exp)

    def _on_special_token(self, token, sync: bool):
        inner: str = self._unwrap_token(token)

        if inner.startswith("end"):
            last = self._ops_stack.pop()
            assert last == inner[3:]
            self._flush()
            self._builder.dedent()

        else:
            op = inner.split(" ", 1)[0]

            if op == "if" or op == "for" or op == "while":
                self._ops_stack.append(op)
                self._flush()
                self._builder.add_line(f"{inner}:")
                self._builder.indent()

            elif op == "else" or op == "elif":
                self._flush()
                self._builder.dedent()
                self._builder.add_line(f"{inner}:")
                self._builder.indent()

            else:
                params: str = self._make_context(inner)
                if sync:
                    self._buffer.append(f"append_result({op}.render({params}))")
                else:
                    self._buffer.append(f"append_result(await {op}.arender({params}))")

    @staticmethod
    def _make_context(text: str):
        """generate context parameter if specified otherwise use locals() by default"""

        return f"dict({text[text.index(' ') + 1:]})" if " " in text else "locals()"

    def compile(self, sync=True):
        self._builder = get_base_builder(sync)

        for token in split_template_tokens(self.text):
            s_token = token.strip()
            if s_token.startswith("{{"):
                self._on_eval_token(token)
            elif s_token.startswith("{#"):
                self._on_exec_token(token)
            elif s_token.startswith("{%"):
                self._on_special_token(token, sync)
            else:
                self._on_literal_token(token)

        if self._ops_stack:
            raise SyntaxError(self._ops_stack)

        self._flush()
        self._builder.add_line("return ''.join(map(str, result))")
        self._builder.dedent()

    @cached_property
    def _render_code(self):
        self.compile()
        return self._builder.get_render_function().__code__

    def render(self, context: Context) -> str:
        return eval(self._render_code, copy(context))

    @cached_property
    def _arender_code(self):
        self.compile(sync=False)
        return self._builder.get_render_function().__code__

    async def arender(self, context: Context) -> str:
        return await eval(self._arender_code, copy(context))


class Loader(AutoNaming):
    @classmethod
    def read(cls, path: str | Path, encoding="utf-8"):
        path = Path(path)
        obj = cls(path.read_text(encoding))
        obj.name = path.stem
        return obj

    @classmethod
    async def aread(cls, path: str | Path, encoding="utf-8"):
        from aiofiles import open

        async with open(path, encoding=encoding) as f:
            content = await f.read()

        path = Path(path)
        obj = cls(content)
        obj.name = path.stem
        return obj

    _client = None

    @classmethod
    def fetch(cls, url: str, **kwargs):
        if cls._client is None:
            from httpx import Client

            cls._client = Client(**kwargs)

        response = cls._client.get(url)
        obj = cls(response.text)
        obj.name = Path(url).stem
        return obj

    _aclient = None

    @classmethod
    async def afetch(cls, url: str, **kwargs):
        if cls._aclient is None:
            from httpx import AsyncClient

            cls._aclient = AsyncClient(**kwargs)

        response = await cls._aclient.get(url)
        obj = cls(response.text)
        obj.name = Path(url).stem
        return obj


class Template(TemplateCore, Loader):
    pass
