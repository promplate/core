from functools import cached_property
from .utils import *
from .builder import *


class Template:
    """A simple template compiler, for a jinja2-like syntax."""

    def __init__(self, text):
        """Construct a Templite with the given `text`."""

        self.text = text
        self.builder = get_base_builder()
        self.buffer = []
        self.ops_stack = []

    def flush(self):
        if len(self.buffer) == 1:
            self.builder.add_line(f"append_result({self.buffer[0]})")
        elif len(self.buffer) > 1:
            self.builder.add_line(f"extend_result(({', '.join(self.buffer)}))")
        self.buffer.clear()

    @staticmethod
    def unwrap_token(token: str):
        return token.strip()[2:-2].strip("-").strip()

    def on_literal_token(self, token: str):
        self.buffer.append(repr(token))

    def on_eval_token(self, token):
        exp = self.unwrap_token(token)
        self.buffer.append(f"repr({exp})")

    def on_comment_token(self, _):
        pass  # TODO: remove blank line

    def on_special_token(self, token):
        inner: str = self.unwrap_token(token)

        if inner.startswith("end"):
            last = self.ops_stack.pop()
            assert last == inner.removeprefix("end")
            self.flush()
            self.builder.dedent()

        else:
            op, _ = inner.split(" ", 1)

            if op == "if" or op == "for":
                self.ops_stack.append(op)
                self.flush()
                self.builder.add_line(f"{inner}:")
                self.builder.indent()

            else:
                raise NotImplementedError(op)

    def compile(self):
        for token in split(self.text):
            s_token = token.strip()
            if not s_token.startswith("{"):
                self.on_literal_token(token)
                continue
            if s_token.startswith("{{"):
                self.on_eval_token(token)
            elif s_token.startswith("{%"):
                self.on_special_token(token)
            else:
                assert s_token.startswith("{#")
                self.on_comment_token(token)

        if self.ops_stack:
            raise SyntaxError(self.ops_stack)

        self.flush()
        self.builder.add_line("return ''.join(result)")
        self.builder.dedent()

    @cached_property
    def render_code(self):
        self.compile()
        return self.builder.get_render_function().__code__

    def render(self, context: dict):
        return eval(self.render_code, context)
