from .prompt import Prompt
from .template import TemplateCore


class Promplate:
    def __init__(self, text: str):
        self.template = TemplateCore(text)

    def get_prompt(self, context):
        return Prompt.from_text(self.template.render(context))
