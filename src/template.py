# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

"""A simple Python template renderer, for a nano-subset of Django syntax.

For a detailed discussion of this code, see this chapter from 500 Lines:
http://aosabook.org/en/500L/a-template-engine.html

"""

# Coincidentally named the same as http://code.activestate.com/recipes/496702/

import re
from functools import cached_property
from os.path import isfile
from typing import Generator


class TemplateSyntaxError(ValueError):
    """Raised when a template has a syntax error."""

    def __init__(self, msg, thing):
        """Raise a syntax error using `msg`, and showing `thing`."""
        super().__init__(f"{msg}: {thing!r}")


class TemplateValueError(ValueError):
    """Raised when an expression won't evaluate in a template."""
    pass


class TemplateContextError(KeyError):
    pass


class CodeBuilder:
    """Build source code conveniently."""

    def __init__(self, indent=0):
        self.code = []
        self.indent_level = indent

    def __str__(self):
        return "".join(map(str, self.code))

    def add_line(self, line):
        """Add a line of source to the code.

        Indentation and newline will be added for you, don't provide them.

        """
        self.code.extend(("\t" * self.indent_level, line, "\n"))

    def add_section(self):
        """Add a section, a sub-CodeBuilder."""
        section = CodeBuilder(self.indent_level)
        self.code.append(section)
        return section

    def indent(self):
        """Increase the current indent for following lines."""
        self.indent_level += 1

    def dedent(self):
        """Decrease the current indent for following lines."""
        self.indent_level -= 1

    def get_globals(self):
        """Execute the code, and return a dict of globals it defines."""
        # A check that the caller really finished all the blocks they started.
        assert self.indent_level == 0
        # Get the Python source as a single string.
        python_source = str(self)
        # Execute the source, defining globals, and return them.
        global_namespace = {}
        exec(python_source, global_namespace)
        return global_namespace


class Template:
    """A simple template renderer, for a nano-subset of Django syntax."""

    def __init__(self, text, *contexts, strict=True):
        """Construct a Templite with the given `text`.

        `contexts` are dictionaries of values to use for future renderings.
        These are good for filters and global values.

        """
        self.context = {}
        for context in contexts:
            self.context.update(context)

        self.text = text
        self.strict = strict
        self.vars_need = set()  # variables must provide
        self.vars_defs = set()  # variables been defined inside template (now loop only)

    @classmethod
    def load_template(cls, path, context=None, *args, **kwargs):
        if not isfile(path):
            raise FileNotFoundError(f"File {path} doesn't exists")

        with open(path, *args, **kwargs) as f:
            text = f.read()

        return Template(text, context or {})

    @cached_property
    def code(self):
        self.vars_need.clear()
        self.vars_defs.clear()

        # We construct a function in source form, then compile it and hold onto
        # it, and execute it to render the template.
        code = CodeBuilder()

        code.add_line("def render_function(context, do_dots, load_template):")
        code.indent()
        vars_code = code.add_section()
        code.add_line("result = []")
        code.add_line("append_result = result.append")
        code.add_line("extend_result = result.extend")
        code.add_line("to_str = str")

        buffered = []

        def flush_output():
            """Force `buffered` to the code builder."""
            if len(buffered) == 1:
                code.add_line(f"append_result({buffered[0]})")
            elif len(buffered) > 1:
                code.add_line(f"extend_result(({', '.join(buffered)}))")
            buffered.clear()

        ops_stack = []

        # Split the text to form a list of tokens.
        tokens = re.split(r"(?s)({{.*?}}|{%.*?%}|{#.*?#})", self.text)

        squash = False

        for token in tokens:
            if token.startswith("{"):
                start, end = 2, -2
                squash = (token[-3] == "-")
                if squash:
                    end = -3

                if token.startswith("{#"):
                    # Comment: ignore it and move on.
                    continue
                elif token.startswith("{{"):
                    # An expression to evaluate.
                    expr = self._expr_code(token[start:end].strip())
                    buffered.append(f"to_str({expr})")
                else:
                    assert token.startswith("{%")
                    # Action tag: split into words and parse further.
                    flush_output()

                    words = token[start:end].strip().split()
                    if words[0] == "if":
                        # An if statement: evaluate the expression to determine if.
                        if len(words) != 2:
                            raise TemplateSyntaxError("Don't understand if", token)
                        ops_stack.append("if")
                        code.add_line(f"if {self._expr_code(words[1])}:")
                        code.indent()
                    elif words[0] == "for":
                        # A loop: iterate over expression result.
                        if len(words) != 4 or words[2] != "in":
                            raise TemplateSyntaxError("Don't understand for", token)
                        ops_stack.append("for")
                        self._declare(words[1])
                        code.add_line(f"for c_{words[1]} in {self._expr_code(words[3])}:")
                        code.indent()
                    elif words[0] == "import":
                        # A component.
                        if len(words) != 4 or words[2] != "as":
                            raise TemplateSyntaxError("Don't understand import", token)
                        path, name = words[1], words[3]
                        self._declare(name)
                        code.add_line(f"c_{name} = load_template({path})")

                    elif words[0] == "slot":
                        code.add_line("yield ''.join(result)")
                        code.add_line("result.clear()")

                    elif words[0].startswith("end"):
                        # End something. Pop the ops stack.
                        if len(words) != 1:
                            raise TemplateSyntaxError("Don't understand end", token)
                        end_what = words[0][3:]
                        if not ops_stack:
                            raise TemplateSyntaxError("Too many ends", token)
                        start_what = ops_stack.pop()
                        if start_what != end_what:
                            raise TemplateSyntaxError("Mismatched end tag", end_what)

                        if end_what == "for" or end_what == "if":
                            code.dedent()
                        else:
                            buffered.append(f"next(c_{end_what}_renderer)")

                    elif words[0] in self.vars_defs:
                        # Use a component.
                        name = words[0]
                        if "~" in words:
                            buffered.append(f"c_{name}.render()")
                        else:
                            ops_stack.append(name)
                            code.add_line(f"c_{name}_renderer = c_{name}.get_renderer()")
                            buffered.append(f"next(c_{name}_renderer)")
                    else:
                        raise TemplateSyntaxError("Don't understand tag", words[0])
            else:
                # Literal content. If it isn't empty, output it.
                if squash:
                    token = token.lstrip()
                if token:
                    buffered.append(repr(token))

        if ops_stack:
            raise TemplateSyntaxError("Unmatched action tag", ops_stack[-1])

        flush_output()

        self.extract_context_to_code(vars_code)

        code.add_line("yield ''.join(result)")
        code.add_line("yield ''")
        code.dedent()

        return code

    def extract_context_to_code(self, code: CodeBuilder):
        if self.strict:
            for var in self.vars_need:
                code.add_line(f"c_{var} = context[{var!r}]")
        else:
            for var in self.vars_need:
                code.add_line(f"c_{var} = context.get({var!r})")

    def _expr_code(self, expr):
        """Generate a Python expression for `expr`."""
        if "|" in expr:
            pipes = expr.split("|")
            code = self._expr_code(pipes[0])
            for func in pipes[1:]:
                self._need(func)
                code = f"c_{func}({code})"
        elif "." in expr:
            dots = expr.split(".")
            code = self._expr_code(dots[0])
            args = ", ".join(repr(d) for d in dots[1:])
            code = f"do_dots({code}, {args})"
        else:
            self._need(expr)
            code = f"c_{expr}"
        return code

    @staticmethod
    def check_naming(name):
        """Raises a syntax error if `name` is not a valid name."""
        if not re.match(r"[_a-zA-Z][_a-zA-Z0-9]*$", name):
            raise TemplateSyntaxError("Not a valid name", name)

    def _declare(self, name):
        """Track that `name` is defined as a variable."""
        self.check_naming(name)
        self.vars_defs.add(name)

    def _need(self, name):
        """Track that `name` is used as a variable."""
        self.check_naming(name)
        if name not in self.vars_defs:  # if it is already declared inside the template
            self.vars_need.add(name)

    @cached_property
    def render_function(self):
        return self.code.get_globals()["render_function"]

    def get_renderer(self, context: dict = None) -> Generator:
        # Make the complete context we'll use.
        render_context = dict(self.context)
        if context:
            render_context.update(context)

        if not self.strict:
            return self.render_function(render_context, self._do_dots, self.load_template)

        # static namespace checking
        render_function = self.render_function
        missing_vars = tuple(v for v in self.vars_need if v not in render_context.keys())
        if missing_vars:
            raise TemplateContextError(f"Missing context: {', '.join(missing_vars)}")
        # noinspection PyCallingNonCallable
        return render_function(render_context, self._do_dots, self.load_template)

    def render(self, context: dict = None):
        return next(self.get_renderer(context))

    @staticmethod
    def _do_dots(value, *dots):
        """Evaluate dotted expressions at run-time."""
        for dot in dots:
            try:
                value = getattr(value, dot)
            except AttributeError:
                try:
                    value = value[dot]
                except (TypeError, KeyError):
                    raise TemplateValueError(f"Couldn't evaluate {value!r}.{dot}")
            if callable(value):
                value = value()
        return value
