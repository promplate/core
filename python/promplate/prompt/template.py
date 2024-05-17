from ast import Expr, parse, unparse
from collections import ChainMap
from functools import cached_property, partial
from pathlib import Path
from sys import path as sys_path
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Literal, Protocol

from .builder import *
from .utils import *

Context = dict[str, Any]  # globals must be a real dict


class Component(Protocol):
    def render(self, context: Context) -> str: ...

    async def arender(self, context: Context) -> str: ...


class TemplateCore(AutoNaming):
    """A simple template compiler, for a jinja2-like syntax."""

    def __init__(self, text: str):
        """Construct a Templite with the given `text`."""

        self.text = text

    def _flush(self):
        for line in self._buffer:
            self._builder.add_line(line)
        self._buffer.clear()

    @staticmethod
    def _unwrap_token(token: str):
        return dedent(token.strip()[2:-2].strip("-")).strip()

    def _on_literal_token(self, token: str):
        self._buffer.append(f"__append__({repr(token)})")

    def _on_eval_token(self, token):
        token = self._unwrap_token(token)
        if "\n" in token:
            mod = parse(token)
            [*rest, last] = mod.body
            assert isinstance(last, Expr), "{{ }} block must end with an expression, or you should use {# #} block"
            self._buffer.extend(unparse(rest).splitlines())  # type: ignore
            exp = unparse(last)
        else:
            exp = token
        self._buffer.append(f"__append__({exp})")

    def _on_exec_token(self, token):
        self._buffer.extend(self._unwrap_token(token).splitlines())

    def _on_special_token(self, token, sync: bool):
        inner = self._unwrap_token(token)

        if inner.startswith("end"):
            last = self._ops_stack.pop()
            assert last == inner.removeprefix("end")
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
                    self._buffer.append(f"__append__({op}.render({params}))")
                else:
                    self._buffer.append(f"__append__(await {op}.arender({params}))")

    @staticmethod
    def _make_context(text: str):
        """generate context parameter if specified otherwise use locals() by default"""

        return f"locals() | dict({text[text.index(' ') + 1:]})" if " " in text else "locals()"

    def compile(self, sync=True, indent_str="\t"):
        self._buffer = []
        self._ops_stack = []
        self._builder = get_base_builder(sync, indent_str)

        for token in split_template_tokens(self.text):
            if not token:
                continue
            s_token = token.strip()
            if s_token.startswith("{{") and s_token.endswith("}}"):
                self._on_eval_token(token)
            elif s_token.startswith("{#") and s_token.endswith("#}"):
                self._on_exec_token(token)
            elif s_token.startswith("{%") and s_token.endswith("%}") and "\n" not in s_token:
                self._on_special_token(token, sync)
            else:
                self._on_literal_token(token)

        if self._ops_stack:
            raise SyntaxError(self._ops_stack)

        self._flush()
        self._builder.add_line("return ''.join(map(str, __parts__))")
        self._builder.dedent()

    error_handling: Literal["linecache", "tempfile", "file"] = "file" if __debug__ else "tempfile"

    def _patch_for_error_handling(self, sync: bool):
        match self.error_handling:
            case "linecache":
                add_linecache(self.name, partial(self.get_script, sync, "\t"))
            case "file" | "tempfile":
                file = save_tempfile(self.name, self.get_script(sync, "\t"), self.error_handling == "tempfile")
                sys_path.append(str(file.parent))

    @cached_property
    def _render_code(self):
        self.compile()
        return self._builder.get_render_function().__code__.replace(co_filename=self.name, co_name="render")

    def render(self, context: Context) -> str:
        try:
            return eval(self._render_code, context)
        except Exception:
            self._patch_for_error_handling(sync=True)
            raise

    @cached_property
    def _arender_code(self):
        self.compile(sync=False)
        return self._builder.get_render_function().__code__.replace(co_filename=self.name, co_name="arender")

    async def arender(self, context: Context) -> str:
        try:
            return await eval(self._arender_code, context)
        except Exception:
            self._patch_for_error_handling(sync=False)
            raise

    def get_script(self, sync=True, indent_str="    "):
        """compile template string into python script"""
        self.compile(sync, indent_str)
        return str(self._builder)


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

    @classmethod
    def _patch_kwargs(cls, kwargs: dict) -> dict:
        return {"headers": {"User-Agent": get_user_agent(cls)}} | kwargs

    @staticmethod
    def _join_url(url: str):
        if url.startswith("http"):
            return url

        from urllib.parse import urljoin

        return urljoin("https://promplate.dev/", url)

    @classmethod
    def fetch(cls, url: str, **kwargs):
        from .utils import _get_client

        response = _get_client().get(cls._join_url(url), **cls._patch_kwargs(kwargs))
        obj = cls(response.raise_for_status().text)
        obj.name = Path(url).stem
        return obj

    @classmethod
    async def afetch(cls, url: str, **kwargs):
        from .utils import _get_aclient

        response = await _get_aclient().get(cls._join_url(url), **cls._patch_kwargs(kwargs))
        obj = cls(response.raise_for_status().text)
        obj.name = Path(url).stem
        return obj


class SafeChainMapContext(ChainMap, dict):
    if TYPE_CHECKING:  # fix type from `collections.ChainMap`
        from sys import version_info

        if version_info >= (3, 11):
            from typing_extensions import Self
        else:
            from typing import Self

        copy: Callable[[Self], Self]


class Template(TemplateCore, Loader):
    def __init__(self, text: str, /, context: Context | None = None):
        super().__init__(text)
        self.context = {} if context is None else context

    def render(self, context: Context | None = None):
        if context is None:
            context = SafeChainMapContext({}, self.context)
        else:
            context = SafeChainMapContext({}, context, self.context)

        return super().render(context)

    async def arender(self, context: Context | None = None):
        if context is None:
            context = SafeChainMapContext({}, self.context)
        else:
            context = SafeChainMapContext({}, context, self.context)

        return await super().arender(context)
