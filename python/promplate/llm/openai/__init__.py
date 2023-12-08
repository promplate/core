from openai.version import VERSION

if VERSION.startswith("0"):
    from .v0 import *
else:
    from .v1 import *
