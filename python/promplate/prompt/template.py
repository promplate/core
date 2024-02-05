from collections import ChainMap
from functools import cached_property
from pathlib import Path
from sys import version_info

from ..typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Protocol, Self, Union
from .builder import get_base_builder
from .utils import AutoNaming, get_user_agent, split_template_tokens

Context = Dict[str, Any]  # globals must be a real dict


class Component(Protocol):
    def render(self, context: Context) -> str: ...

    async def arender(self, context: Context) -> str: ...


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
        self._buffer.append(f"__append__({repr(token)})")

    def _on_eval_token(self, token):
        exp = self._unwrap_token(token)
        self._buffer.append(f"__append__({exp})")

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
                    self._buffer.append(f"__append__({op}.render({params}))")
                else:
                    self._buffer.append(f"__append__(await {op}.arender({params}))")

    @staticmethod
    def _make_context(text: str):
        """generate context parameter if specified otherwise use locals() by default"""
        if version_info >= (3, 10):
            return f"(__l__:=locals().copy(), __l__.update(dict({text[text.index(' ') + 1:]})))[0]" if " " in text else "locals()"
        return f"(__l__:=globals().copy(), __l__.update(dict({text[text.index(' ') + 1:]})))[0]" if " " in text else "globals()"

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
        self._builder.add_line("return ''.join(map(str, __parts__))")
        self._builder.dedent()

    @cached_property
    def _render_code(self):
        self.compile()
        return self._builder.get_render_function().__code__.replace(co_filename=str(self), co_name="render")

    def render(self, context: Context) -> str:
        return eval(self._render_code, context)

    @cached_property
    def _arender_code(self):
        self.compile(sync=False)
        return self._builder.get_render_function().__code__.replace(co_filename=str(self), co_name="arender")

    async def arender(self, context: Context) -> str:
        return await eval(self._arender_code, context)

    def get_script(self, sync=True):
        """compile template string into python script"""
        self.compile(sync)
        return str(self._builder)


class Loader(AutoNaming):
    @classmethod
    def read(cls, path: Union[str, Path], encoding="utf-8"):
        path = Path(path)
        obj = cls(path.read_text(encoding))
        obj.name = path.stem
        return obj

    @classmethod
    async def aread(cls, path: Union[str, Path], encoding="utf-8"):
        from aiofiles import open

        async with open(path, encoding=encoding) as f:
            content = await f.read()

        path = Path(path)
        obj = cls(content)
        obj.name = path.stem
        return obj

    @classmethod
    def _patch_kwargs(cls, kwargs: dict):
        return {
            **{
                "follow_redirects": True,
                "base_url": "https://promplate.dev/",
                "headers": {"User-Agent": get_user_agent(cls)},
            },
            **kwargs,
        }

    @classmethod
    def fetch(cls, url: str, **kwargs):
        from .utils import _get_client

        response = _get_client().get(url, **cls._patch_kwargs(kwargs))
        obj = cls(response.raise_for_status().text)
        obj.name = Path(url).stem
        return obj

    @classmethod
    async def afetch(cls, url: str, **kwargs):
        from .utils import _get_aclient

        response = await _get_aclient().get(url, **cls._patch_kwargs(kwargs))
        obj = cls(response.raise_for_status().text)
        obj.name = Path(url).stem
        return obj


class SafeChainMapContext(ChainMap, dict):
    if TYPE_CHECKING:  # fix type from `collections.ChainMap`
        from sys import version_info

        copy: Callable[[Self], Self]


class Template(TemplateCore, Loader):
    def __init__(self, text: str, /, context: Optional[Context] = None):
        super().__init__(text)
        self.context = {} if context is None else context

    def render(self, context: Optional[Context] = None):
        if context is None:
            context = SafeChainMapContext({}, self.context)
        else:
            context = SafeChainMapContext({}, context, self.context)

        return super().render(context)

    async def arender(self, context: Optional[Context] = None):
        if context is None:
            context = SafeChainMapContext({}, self.context)
        else:
            context = SafeChainMapContext({}, context, self.context)

        return await super().arender(context)
