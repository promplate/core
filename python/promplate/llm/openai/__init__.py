from openai.version import VERSION

if VERSION.startswith("1"):
    from .v1 import *
else:
    from .v0 import *
