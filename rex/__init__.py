"""Rex — a tiny, friendly scripting language for API work. Made in Mzansi 🇿🇦

>>> from rex import run
>>> run('rex.show("Sawubona Mhlaba")')
['Sawubona Mhlaba']
"""

__version__ = "1.0.1"
__author__ = "Andile Mtolo (Toxic Dee Modder)"
__license__ = "MIT"

from .errors import (  # noqa: E402
    RexError,
    RexImportError,
    RexRuntimeError,
    RexSyntaxError,
)
from .interpreter import RexInterpreter, run  # noqa: E402
from .parser import parse, parse_expression  # noqa: E402

__all__ = [
    "RexError",
    "RexSyntaxError",
    "RexRuntimeError",
    "RexImportError",
    "RexInterpreter",
    "parse",
    "parse_expression",
    "run",
    "__version__",
]
