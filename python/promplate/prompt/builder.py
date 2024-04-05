from types import FunctionType


class CodeBuilder:
    """Build source code conveniently."""

    def __init__(self, indent_level=0, indent_str="\t"):
        self.code = []
        self.indent_level = indent_level
        self.indent_str = indent_str

    def __str__(self):
        return "".join(map(str, self.code))

    def add_line(self, line):
        """Add a line of source to the code."""
        self.code.extend((self.indent_str * self.indent_level, line, "\n"))

        return self

    def add_section(self):
        """Add a section, a sub-CodeBuilder."""
        section = CodeBuilder(self.indent_level, self.indent_str)
        self.code.append(section)

        return section

    def indent(self):
        """Increase the current indent for following lines."""
        self.indent_level += 1

        return self

    def dedent(self):
        """Decrease the current indent for following lines."""
        self.indent_level -= 1

        return self

    def get_render_function(self) -> FunctionType:
        """Execute the code, and return a dict of globals it defines."""
        assert self.indent_level == 0
        python_source = str(self)
        global_namespace = {}
        exec(python_source, global_namespace)
        return global_namespace["render"]


def get_base_builder(sync=True, indent_str="\t"):
    return (
        CodeBuilder(indent_str=indent_str)
        .add_line("def render():" if sync else "async def render():")
        .indent()
        .add_line("__parts__ = []")
        .add_line("__append__ = __parts__.append")
    )
