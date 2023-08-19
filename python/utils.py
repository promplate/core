from re import compile

splitter = compile(
    r"(\s{%-.*?-%}\s|\s{{-.*?-}}\s|\s{#-.*?-#}\s|\s{%-.*?%}|\s{{-.*?}}|\s{#-.*?#}|{%.*?-%}\s|{{.*?-}}\s|{#.*?-#}\s|{%.*?%}|{{.*?}}|{#.*?#})"
)


var_name_checker = compile(r"[_a-zA-Z]\w*$")

is_message_start = compile(r"<\|\s?(user|system|assistant)\s?(\w{1,64})?\s?\|>")


def split(text: str) -> list[str]:
    return splitter.split(text)


def is_not_valid(name: str):
    return not var_name_checker.match(name)


def ensure_valid(name):
    if is_not_valid(name):
        raise NameError(name)
