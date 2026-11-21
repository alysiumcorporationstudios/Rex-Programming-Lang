"""MkDocs hook: teach Pygments about `.rex` so code fences are highlighted.

MkDocs adds the hook's own directory to `sys.path` only while executing this
module and then restores it, so the lexer is imported and registered eagerly
here rather than lazily by Pygments later.
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:  # pragma: no cover - only runs during a docs build
    from pygments.lexers import _lexer_cache
    from pygments.lexers._mapping import LEXERS
    from rex_lexer import RexLexer

    # (module, cache key, aliases, filenames, mimetypes)
    LEXERS["RexLexer"] = ("rex_lexer", "Rex", ("rex",), ("*.rex",), ("text/x-rex",))
    _lexer_cache["Rex"] = RexLexer
except Exception as error:  # pragma: no cover
    print("warning: could not register the Rex lexer: %s" % error, file=sys.stderr)


def on_config(config):  # noqa: ANN001, ARG001 - mkdocs hook signature
    """Called once before the site is built."""
    return config
