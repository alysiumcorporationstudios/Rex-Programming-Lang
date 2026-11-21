"""Rex error types and pretty-printed diagnostics.

Every error Rex raises carries an optional source position so the CLI can render
a compiler-style snippet with a caret under the offending token.
"""

from __future__ import annotations

from typing import Optional


class RexError(Exception):
    """Base class for every error Rex raises on purpose."""

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        col: Optional[int] = None,
        length: int = 1,
        filename: Optional[str] = None,
        source: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col
        self.length = max(1, length)
        self.filename = filename
        self.source = source
        self.hint = hint

    def with_position(self, line: Optional[int], col: Optional[int], filename: Optional[str] = None, source: Optional[str] = None, length: int = 1) -> "RexError":
        """Attach a position if the error does not have one yet."""
        if self.line is None:
            self.line = line
            self.col = col
            self.length = max(1, length)
        if self.filename is None:
            self.filename = filename
        if self.source is None:
            self.source = source
        return self

    def render(self) -> str:
        """Return the multi-line, human friendly rendering of this error."""
        head = "Rex Error: " + self.message
        if self.hint:
            head += "\n  hint: " + self.hint
        if self.line is None:
            return head
        location = self.filename or "<input>"
        parts = ["  --> %s:%d:%d" % (location, self.line, self.col or 1)]
        if self.source:
            lines = self.source.splitlines()
            if 0 < self.line <= len(lines):
                text = lines[self.line - 1]
                gutter = str(self.line)
                pad = " " * len(gutter)
                parts.append("%s |" % pad)
                parts.append("%s | %s" % (gutter, text))
                caret_col = max(1, self.col or 1)
                caret_len = min(self.length, max(1, len(text) - caret_col + 1))
                parts.append("%s | %s%s" % (pad, " " * (caret_col - 1), "^" * caret_len))
        return head + "\n" + "\n".join(parts)


class RexSyntaxError(RexError):
    """Raised when source text cannot be tokenised or parsed."""


class RexRuntimeError(RexError):
    """Raised when a well-formed program fails while running."""


class RexImportError(RexRuntimeError):
    """Raised when `rex.import` cannot load a file."""


class ReturnSignal(Exception):
    """Internal control-flow signal for `rex.return`."""

    def __init__(self, value: object) -> None:
        self.value = value


class BreakSignal(Exception):
    """Internal control-flow signal for `rex.break`."""


class ContinueSignal(Exception):
    """Internal control-flow signal for `rex.continue`."""


class ExitSignal(Exception):
    """Internal control-flow signal for `rex.exit(code)`."""

    def __init__(self, code: int) -> None:
        self.code = code
