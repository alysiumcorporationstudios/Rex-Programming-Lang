"""A Pygments lexer for Rex, used by the documentation site.

Registering it means ```rex fences are highlighted properly instead of being
rendered as plain text.
"""

from pygments.lexer import RegexLexer, include
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Text,
    Whitespace,
)

__all__ = ["RexLexer"]

CONTROL = {
    "let", "if", "elif", "else", "end", "while", "for", "func",
    "return", "break", "continue", "try", "catch", "throw", "import", "pass",
}


def _rex_member(lexer, match):
    """Colour `rex.` as a namespace and the member as keyword or builtin."""
    member = match.group(5)
    yield match.start(), Name.Namespace, match.group(1)
    yield match.start(2), Whitespace, match.group(2)
    yield match.start(3), Punctuation, match.group(3)
    yield match.start(4), Whitespace, match.group(4)
    yield match.start(5), Keyword if member in CONTROL else Name.Builtin, member


def _rex_func(lexer, match):
    """Colour the name in `rex.func name(` as a function definition."""
    yield match.start(), Name.Namespace, match.group(1)
    yield match.start(2), Punctuation, match.group(2)
    yield match.start(3), Keyword, match.group(3)
    yield match.start(4), Whitespace, match.group(4)
    yield match.start(5), Name.Function, match.group(5)


class RexLexer(RegexLexer):
    """Pygments lexer for the Rex scripting language."""

    name = "Rex"
    aliases = ["rex"]
    filenames = ["*.rex"]
    mimetypes = ["text/x-rex"]

    tokens = {
        "root": [
            (r"[ \t]+", Whitespace),
            (r"#[^\n]*", Comment.Single),
            (r"\b(rex)(\.)(func)(\s+)([A-Za-z_]\w*)", _rex_func),
            (r"\b(rex)(\s*)(\.)(\s*)([A-Za-z_]\w*)", _rex_member),
            (r"\b(true|false|null)\b", Keyword.Constant),
            (r"\b(and|or|not|in)\b", Operator.Word),
            (r"\d[\d_]*\.\d[\d_]*([eE][+-]?\d+)?", Number.Float),
            (r"\d[\d_]*([eE][+-]?\d+)?", Number.Integer),
            (r"[A-Za-z_]\w*", Name),
            (r'"', String.Double, "double-string"),
            (r"'", String.Single, "single-string"),
            (r"==|!=|<=|>=|&&|\|\||[+\-*/%=<>!]", Operator),
            (r"[(){}\[\],.:;]", Punctuation),
            include("whitespace"),
        ],
        "double-string": [
            (r'[^"\\$]+', String.Double),
            (r"\\.", String.Escape),
            (r"\$\{[^}]*\}", String.Interpol),
            (r'"', String.Double, "#pop"),
        ],
        "single-string": [
            (r"[^'\\]+", String.Single),
            (r"\\.", String.Escape),
            (r"'", String.Single, "#pop"),
        ],
        "whitespace": [
            (r"\n", Text),
            (r".", Text),
        ],
    }
