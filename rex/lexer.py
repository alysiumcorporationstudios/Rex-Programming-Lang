"""Hand written lexer for Rex.

The lexer is intentionally small and dependency free. It produces a flat list of
`Token` objects and keeps track of bracket depth so that expressions can be
spread over several lines without turning into syntax errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .errors import RexSyntaxError

# Token kinds
NUMBER = "NUMBER"
STRING = "STRING"
NAME = "NAME"
OP = "OP"
NEWLINE = "NEWLINE"
EOF = "EOF"

# Longest operators first so `==` wins over `=`.
_OPERATORS = [
    "==", "!=", "<=", ">=", "&&", "||", "**",
    "+", "-", "*", "/", "%", "=", "<", ">", "!",
    "(", ")", "[", "]", "{", "}", ",", ".", ":", ";", "?",
]

_OPENERS = {"(", "[", "{"}
_CLOSERS = {")", "]", "}"}
_MATCHING = {")": "(", "]": "[", "}": "{"}

# After one of these a newline is a continuation, not a statement break.
_CONTINUATION_TOKENS = {
    ",", "+", "-", "*", "/", "%", "=", "==", "!=", "<", ">", "<=", ">=",
    "&&", "||", "!", "and", "or", "not", ":", ".", "(", "[", "{", "?",
}

_ESCAPES = {
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "0": "\0",
    "\\": "\\",
    '"': '"',
    "'": "'",
    "b": "\b",
    "f": "\f",
    "/": "/",
}


@dataclass
class Token:
    kind: str
    value: str
    line: int
    col: int
    length: int = 1
    interpolated: bool = False
    literal: object = None

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return "Token(%s, %r, %d:%d)" % (self.kind, self.value, self.line, self.col)


def tokenize(source: str, filename: str = "<input>") -> List[Token]:
    """Turn Rex source text into a list of tokens ending with EOF."""
    tokens: List[Token] = []
    i = 0
    line = 1
    col = 1
    depth = 0
    length = len(source)

    def add(kind: str, value: str, tline: int, tcol: int, tlen: int = 1, **kwargs) -> None:
        tokens.append(Token(kind, value, tline, tcol, tlen, **kwargs))

    def last_significant():
        for tok in reversed(tokens):
            if tok.kind != NEWLINE:
                return tok
        return None

    while i < length:
        ch = source[i]

        # Newlines -------------------------------------------------------
        if ch in "\r\n":
            if ch == "\r" and i + 1 < length and source[i + 1] == "\n":
                i += 1
            start_line, start_col = line, col
            i += 1
            line += 1
            col = 1
            if depth == 0:
                prev = last_significant()
                if prev is None or prev.kind == NEWLINE or prev.value in _CONTINUATION_TOKENS:
                    continue
                add(NEWLINE, "\n", start_line, start_col)
            continue

        # Whitespace -----------------------------------------------------
        if ch in " \t\f\v":
            i += 1
            col += 1
            continue

        # Comments -------------------------------------------------------
        if ch == "#":
            while i < length and source[i] not in "\r\n":
                i += 1
                col += 1
            continue

        # Line continuation ---------------------------------------------
        if ch == "\\" and i + 1 < length and source[i + 1] in "\r\n":
            i += 1
            if source[i] == "\r" and i + 1 < length and source[i + 1] == "\n":
                i += 1
            i += 1
            line += 1
            col = 1
            continue

        # Numbers --------------------------------------------------------
        if ch.isdigit():
            start_i, start_col = i, col
            while i < length and (source[i].isdigit() or source[i] == "_"):
                i += 1
                col += 1
            is_float = False
            if i < length and source[i] == "." and i + 1 < length and source[i + 1].isdigit():
                is_float = True
                i += 1
                col += 1
                while i < length and (source[i].isdigit() or source[i] == "_"):
                    i += 1
                    col += 1
            if i < length and source[i] in "eE":
                j = i + 1
                if j < length and source[j] in "+-":
                    j += 1
                if j < length and source[j].isdigit():
                    is_float = True
                    col += j - i
                    i = j
                    while i < length and source[i].isdigit():
                        i += 1
                        col += 1
            text = source[start_i:i].replace("_", "")
            value = float(text) if is_float else int(text)
            add(NUMBER, text, line, start_col, i - start_i, literal=value)
            continue

        # Identifiers ----------------------------------------------------
        if ch.isalpha() or ch == "_":
            start_i, start_col = i, col
            while i < length and (source[i].isalnum() or source[i] == "_"):
                i += 1
                col += 1
            add(NAME, source[start_i:i], line, start_col, i - start_i)
            continue

        # Strings --------------------------------------------------------
        if ch in "\"'":
            quote = ch
            start_line, start_col = line, col
            start_i = i
            i += 1
            col += 1
            chunks: List[str] = []
            while True:
                if i >= length:
                    raise RexSyntaxError(
                        "unterminated string literal",
                        line=start_line, col=start_col, filename=filename, source=source,
                    )
                cur = source[i]
                if cur == quote:
                    i += 1
                    col += 1
                    break
                if cur in "\r\n":
                    raise RexSyntaxError(
                        "unterminated string literal (strings cannot span lines, use \\n)",
                        line=start_line, col=start_col, filename=filename, source=source,
                    )
                if cur == "\\":
                    if i + 1 >= length:
                        raise RexSyntaxError(
                            "unterminated string literal",
                            line=start_line, col=start_col, filename=filename, source=source,
                        )
                    nxt = source[i + 1]
                    if nxt == "u" and i + 5 < length:
                        hexpart = source[i + 2:i + 6]
                        try:
                            chunks.append(chr(int(hexpart, 16)))
                            i += 6
                            col += 6
                            continue
                        except ValueError:
                            pass
                    chunks.append(_ESCAPES.get(nxt, nxt))
                    i += 2
                    col += 2
                    continue
                chunks.append(cur)
                i += 1
                col += 1
            raw = "".join(chunks)
            add(
                STRING, raw, start_line, start_col, i - start_i,
                interpolated=(quote == '"'),
            )
            continue

        # Operators and punctuation -------------------------------------
        matched = None
        for op in _OPERATORS:
            if source.startswith(op, i):
                matched = op
                break
        if matched is None:
            raise RexSyntaxError(
                "unexpected character %r" % ch,
                line=line, col=col, filename=filename, source=source,
            )

        if matched in _OPENERS:
            depth += 1
        elif matched in _CLOSERS:
            depth = max(0, depth - 1)
        add(OP, matched, line, col, len(matched))
        i += len(matched)
        col += len(matched)

    if depth > 0:
        raise RexSyntaxError(
            "unclosed bracket: %d unclosed opening bracket(s) at end of file" % depth,
            line=line, col=col, filename=filename, source=source,
        )

    tokens.append(Token(NEWLINE, "\n", line, col))
    tokens.append(Token(EOF, "", line, col))
    return tokens


def describe_token(tok: Token) -> str:
    """Short human readable description used in parser error messages."""
    if tok.kind == EOF:
        return "end of file"
    if tok.kind == NEWLINE:
        return "end of line"
    if tok.kind == STRING:
        return "string %r" % tok.value
    return "%r" % tok.value
