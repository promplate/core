from functools import cache, cached_property, wraps
from inspect import currentframe, isclass
from pathlib import Path
from re import compile
from typing import Any, Callable, ParamSpec, TypeVar

split_template_tokens = compile(
    r"((?:\s{%-|{%).*?(?:%}|-%}\s))|((?:\s{{-|{{)[\s\S]*?(?:}}|-}}\s))|((?:\s{#-|{#)[\s\S]*?(?:#}|-#}\s))"
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

    def _bind_frame(self):
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


P = ParamSpec("P")
T = TypeVar("T")


def cache_once(func: Callable[P, T]) -> Callable[P, T]:
    result = None

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        nonlocal result
        if result is None:
            result = func(*args, **kwargs)
        return result

    return wrapper


@cache_once
def get_builtins() -> dict[str, Any]:
    return __builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__


@cache
def version(package: str):
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version(package)
    except PackageNotFoundError:
        return None


@cache_once
def get_user_agent(self, *additional_packages: tuple[str, str]):
    from sys import version as py_version

    return " ".join(
        (
            f"Promplate/{version('promplate')} ({self.__name__ if isclass(self) else self.__class__.__name__})",
            *(f"{name}/{v}" for name, v in additional_packages),
            f"HTTPX/{version('httpx') or '-'}",
            f"Python/{py_version.split()[0]}",
        )
    )


@cache_once
def _is_http2_available():
    try:
        import h2  # type: ignore

        return True
    except ImportError:
        return False


@cache_once
def _get_client():
    from httpx import Client

    return Client(follow_redirects=True, http2=_is_http2_available())


@cache_once
def _get_aclient():
    from httpx import AsyncClient

    return AsyncClient(follow_redirects=True, http2=_is_http2_available())


def add_linecache(filename: str, source_getter: Callable[[], str]):
    import linecache

    linecache.cache[filename] = (source_getter,)


def save_tempfile(filename: str, source: str, auto_deletion: bool):
    from tempfile import mkdtemp

    file = Path(mkdtemp(prefix="promplate-")) / filename
    file.write_text(source)

    if auto_deletion:
        import atexit

        @atexit.register
        def _():
            file.unlink(missing_ok=True)
            file.parent.rmdir()

    return file
