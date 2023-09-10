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
        if len(self._buffer) == 1:
            self._builder.add_line(f"append_result({self._buffer[0]})")
        elif len(self._buffer) > 1:
            self._builder.add_line(f"extend_result(({', '.join(self._buffer)}))")
        self._buffer.clear()

    @staticmethod
    def _unwrap_token(token: str):
        return token.strip()[2:-2].strip("-").strip()

    def _on_literal_token(self, token: str):
        self._buffer.append(repr(token))

    def _on_eval_token(self, token):
        exp = self._unwrap_token(token)
        self._buffer.append(f"str({exp})")

    def _on_comment_token(self, _):
        pass  # TODO: remove blank line

    def _on_special_token(self, token, sync: bool):
        inner: str = self._unwrap_token(token)

        if inner.startswith("end"):
            last = self._ops_stack.pop()
            assert last == inner.removeprefix("end")
            self._flush()
            self._builder.dedent()

        else:
            op = inner.split(" ", 1)[0]

            if op == "if" or op == "for":
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
                arguments: str = self._make_context(inner)
                if sync:
                    self._buffer.append(f"{op}.render({arguments})")
                else:
                    self._buffer.append(f"await {op}.arender({arguments})")

    @staticmethod
    def _make_context(text: str):
        pairs = []
        for token in text.split(" ")[1:]:
            if token == "*":
                pairs.append("**locals()")
            elif "=" in token or token.startswith("**"):
                pairs.append(token)
            else:
                pairs.append(f"{token}={token}")

        return f"dict({', '.join(pairs)})"

    def compile(self, sync=True):
        self._builder = get_base_builder(sync)

        for token in split_template_tokens(self.text):
            s_token = token.strip()
            if not s_token.startswith("{"):
                self._on_literal_token(token)
                continue
            if s_token.startswith("{{"):
                self._on_eval_token(token)
            elif s_token.startswith("{%"):
                self._on_special_token(token, sync)
            else:
                assert s_token.startswith("{#")
                self._on_comment_token(token)

        if self._ops_stack:
            raise SyntaxError(self._ops_stack)

        self._flush()
        self._builder.add_line("return ''.join(result)")
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


class Template(TemplateCore):
    @classmethod
    def read(cls, path: str | Path, encoding="utf-8"):
        path = Path(path)
        template = cls(path.read_text(encoding))
        template.name = path.stem
        return template

    @classmethod
    async def aread(cls, path: str | Path, encoding="utf-8"):
        from aiofiles import open

        async with open(path, encoding=encoding) as f:
            content = await f.read()

        path = Path(path)
        template = cls(content)
        template.name = path.stem
        return template

    _client = None

    @classmethod
    def fetch(cls, url: str, **kwargs):
        if cls._client is None:
            from httpx import Client

            cls._client = Client(**kwargs)

        response = cls._client.get(url)
        template = cls(response.text)
        template.name = Path(url).stem
        return template

    _aclient = None

    @classmethod
    async def afetch(cls, url: str, **kwargs):
        if cls._aclient is None:
            from httpx import AsyncClient

            cls._aclient = AsyncClient(**kwargs)

        response = await cls._aclient.get(url)
        template = cls(response.text)
        template.name = Path(url).stem
        return template
