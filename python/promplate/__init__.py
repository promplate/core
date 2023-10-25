try:
    from .chain import *
    from .prompt import *

except TypeError:
    from .compatible import *
