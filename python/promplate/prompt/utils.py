from functools import cached_property
from inspect import currentframe
from re import compile

split_template_tokens = compile(
    r"(\s{%-.*?-%}\s|\s{{-.*?-}}\s|\s{#-.*?-#}\s|\s{%-.*?%}|\s{{-.*?}}|\s{#-.*?#}|{%.*?-%}\s|{{.*?-}}\s|{#.*?-#}\s|{%.*?%}|{{.*?}}|{#.*?#})"
).split


var_name_checker = compile(r"[_a-zA-Z]\w*$")

is_message_start = compile(r"<\|\s?(user|system|assistant)\s?(\w{1,64})?\s?\|>")


def is_not_valid(name: str):
    return not var_name_checker.match(name)


def ensure_valid(name):
    if is_not_valid(name):
        raise NameError(name)


class AutoNaming:
    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj._bind_frame()
        return obj

    def _bind_frame(self) -> None:
        self._frame = currentframe()

    @cached_property
    def _name(self):
        f = self._frame
        if f and f.f_back and (frame := f.f_back.f_back):
            for name, var in frame.f_locals.items():
                if var is self:
                    return name

    @property
    def class_name(self):
        return self.__class__.__name__

    fallback_name = class_name

    @property
    def name(self):
        return self._name or self.fallback_name

    @name.setter
    def name(self, name):
        self._name = name
        self._frame = None

    @name.deleter
    def name(self):
        del self._name

    def __repr__(self):
        if self._name:
            return f"<{self.class_name} {self.name}>"
        else:
            return f"<{self.class_name}>"

    def __str__(self):
        return f"<{self.name}>"
