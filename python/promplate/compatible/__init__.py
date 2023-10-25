from typing import Dict
import re
import os


def compat_convert(code: str) -> str:
    """
    Convert Python 3.10+ code to Python 3.8+ code.
    """

    # convert `list` type annotation to `List`
    code = re.sub(r"(:|->) list\[([a-zA-Z0-9_]+) \| ([a-zA-Z0-9_]+)\]", r"\1 List[Union[\2, \3]]", code)
    code = re.sub(r"(:|->) list\[([a-zA-Z0-9_]+)\]", r"\1 List[\2]", code)

    # convert `|` type annotation to `Union`
    code = re.sub(r"(:|->) ([a-zA-Z0-9_]+) \| ([a-zA-Z0-9_]+) \| ([a-zA-Z0-9_]+)", r"\1 Union[\2, \3, \4]", code)
    code = re.sub(r"(:|->) ([a-zA-Z0-9_]+) \| (List\[[a-zA-Z0-9_]+\])  \| ([a-zA-Z0-9_]+)", r"\1 Union[\2, \3, \4]", code)
    code = re.sub(r"(:|->) ([a-zA-Z0-9_]+) \| ([a-zA-Z0-9_]+)", r"\1 Union[\2, \3]", code)
    code = re.sub(r"(:|->) (List\[[a-zA-Z0-9_]+\]) \| ([a-zA-Z0-9_]+)", r"\1 Union[\2, \3]", code)

    # convert miscellany
    code = code.replace("NotRequired", "Optional")
    code = code.replace("MutableMapping[Any, Any] | None", "Union[MutableMapping[Any, Any], None]")
    code = code.replace("Mapping[Any, Any] | None", "Union[Mapping[Any, Any], None]")
    code = code.replace("CTX | None", "Union[CTX, None]")
    code = code.replace("List[Union[Process, AsyncProcess]] | None", "Union[List[Union[Process, AsyncProcess]], None]")
    code = code.replace("dict[str, Any]", "Dict[str, Any]")

    # add typing import
    code = "from typing import *\n" + code

    # replace `promplate` with `promplate.compatible`
    code = code.replace("from promplate", "from promplate.compatible")

    return code


def file_list(root: str) -> Dict[str, str]:
    """
    Return a dictionary of all Python files (except this file) under `promplate` directory.
    This is used to convert all files in `promplate/` to `promplate/compatible/`.
    """

    assert os.path.basename(root) == "promplate" or os.path.basename(root) == "tests"

    files = {}
    for path, _, filenames in os.walk(root):
        if not path.startswith(os.path.join(root, "compatible")):
            for filename in filenames:
                if filename.endswith(".py"):
                    old_path = os.path.join(path, filename)
                    new_path = os.path.join(
                        root, "compatible", path[len(root) + 1:], filename
                    )
                    files[old_path] = new_path

    # remove `promplate/compatible/__init__.py`
    if __file__ in files:
        files.pop(__file__)

    return files


def file_list_convert(file_list: Dict[str, str]):
    """
    Convert all files in `promplate/` to `promplate/compatible/`.
    """

    for old_file, new_file in file_list.items():
        with open(old_file, "r", encoding="utf-8-sig") as f:
            code = f.read()
        code = compat_convert(code)

        os.makedirs(os.path.dirname(new_file), exist_ok=True)

        with open(new_file, "w", encoding="utf-8-sig") as f:
            f.write(code)


try:
    from .chain import *
    from .prompt import *

except ImportError:
    # convert all files in `promplate/` to `promplate/compatible/`.
    root = os.path.dirname(os.path.dirname(__file__))
    file_list_convert(file_list(root))

    from .chain import *
    from .prompt import *
