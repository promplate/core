from sys import version_info

if version_info >= (3, 12):
    from typing import *
else:
    from typing_extensions import *
