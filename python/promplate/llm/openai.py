from openai import ChatCompletion, Completion
from promplate.prompt.chat import Message


def text_complete(**default_config):
    def complete_text(text: str, **config) -> str:
        config = default_config | config
        res = Completion.create(prompt=text, **config)
        return res["choices"][0]["text"]

    return complete_text


def async_text_complete(**default_config):
    async def async_complete_text(text: str, **config) -> str:
        config = default_config | config
        res = await Completion.acreate(prompt=text, **config)
        return res["choices"][0]["text"]

    return async_complete_text


def chat_complete(**default_config):
    def complete_chat(messages: list[Message], **config) -> str:
        config = default_config | config
        res = ChatCompletion.create(messages=messages, **config)
        return res["choices"][0]["message"]["content"]

    return complete_chat


def async_chat_complete(**default_config):
    async def async_complete_chat(messages: list[Message], **config) -> str:
        config = default_config | config
        res = await ChatCompletion.acreate(messages=messages, **config)
        return res["choices"][0]["message"]["content"]

    return async_complete_chat
