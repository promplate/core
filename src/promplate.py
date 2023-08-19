from .prompt import Prompt
from .template import Template


class Promplate:
    def __init__(self, text: str):
        self.template = Template(text)

    def get_prompt(self, context):
        return Prompt.from_text(self.template.render(context))
