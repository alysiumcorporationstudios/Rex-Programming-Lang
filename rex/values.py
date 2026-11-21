"""Runtime values shared by the interpreter and the standard library."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from .errors import RexError

MAX_DISPLAY_DEPTH = 12


class Namespace(dict):
    """A `rex.<something>` group such as `rex.json` or `rex.math`."""

    def __init__(self, name: str, **items: Any) -> None:
        super().__init__(items)
        self.name = name


@dataclass
class Builtin:
    """A native function exposed on the `rex` namespace."""

    name: str
    fn: Callable[..., Any]
    min_args: int = 0
    max_args: Optional[int] = None
    doc: str = ""

    def call(self, args: List[Any], line: int = 0, col: int = 1, source: str = "", filename: str = "") -> Any:
        count = len(args)
        if count < self.min_args:
            raise RexError(
                "%s() expects at least %d argument(s), got %d" % (self.name, self.min_args, count),
                line=line, col=col, source=source, filename=filename,
            )
        if self.max_args is not None and count > self.max_args:
            expected = (
                str(self.min_args)
                if self.min_args == self.max_args
                else "%d to %d" % (self.min_args, self.max_args)
            )
            raise RexError(
                "%s() expects %s argument(s), got %d" % (self.name, expected, count),
                line=line, col=col, source=source, filename=filename,
            )
        try:
            return self.fn(*args)
        except RexError as exc:
            raise exc.with_position(line, col, filename or None, source or None) from None
        except (TypeError, ValueError, OSError, KeyError, IndexError) as exc:
            raise RexError(
                "%s(): %s" % (self.name, exc),
                line=line, col=col, source=source, filename=filename,
            ) from None

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return "<builtin %s>" % self.name


@dataclass
class RexFunction:
    """A user defined function created with `rex.func`."""

    name: str
    params: List[Any]  # list of (name, default_node_or_None)
    body: List[Any]
    closure: Any
    filename: str = "<input>"
    source: str = ""
    line: int = 0

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return "<function %s>" % self.name


def describe_type(value: Any) -> str:
    """Return the Rex type name of a Python value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, RexFunction):
        return "function"
    if isinstance(value, Builtin):
        return "builtin"
    return type(value).__name__


def format_number(value: float) -> str:
    """Format a number the way Rex prints it (no trailing .0 for whole floats)."""
    if isinstance(value, bool):  # pragma: no cover - guarded by callers
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if value != value:  # NaN
        return "nan"
    if value in (float("inf"), float("-inf")):
        return "inf" if value > 0 else "-inf"
    if float(value).is_integer() and abs(value) < 1e16:
        return str(int(value))
    return repr(value)


def format_value(value: Any, indent: int = 2, pretty: bool = True, depth: int = 0) -> str:
    """Human readable rendering used by `rex.show` and string interpolation."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return format_number(value)
    if isinstance(value, str):
        return value
    if isinstance(value, (list, dict)):
        if depth > MAX_DISPLAY_DEPTH:
            return "..."
        try:
            return json.dumps(value, indent=indent if pretty else None, ensure_ascii=False, default=_json_default)
        except (TypeError, ValueError):
            return repr(value)
    if isinstance(value, RexFunction):
        return "<function %s>" % value.name
    if isinstance(value, Builtin):
        return "<builtin %s>" % value.name
    return repr(value)


def _json_default(obj: Any) -> Any:
    if isinstance(obj, RexFunction):
        return "<function %s>" % obj.name
    if isinstance(obj, Builtin):
        return "<builtin %s>" % obj.name
    return repr(obj)


def truthy(value: Any) -> bool:
    """Rex truthiness: null, false, 0, '', [], {} and 0.0 are false."""
    if value is None or value is False:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return len(value) > 0
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def equals(left: Any, right: Any) -> bool:
    """Structural equality that keeps booleans distinct from numbers."""
    if left is None or right is None:
        return left is None and right is None
    left_bool = isinstance(left, bool)
    right_bool = isinstance(right, bool)
    if left_bool or right_bool:
        return left_bool and right_bool and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if isinstance(left, str) and isinstance(right, str):
        return left == right
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return False
        return all(equals(a, b) for a, b in zip(left, right))
    if isinstance(left, dict) and isinstance(right, dict):
        if set(left.keys()) != set(right.keys()):
            return False
        return all(equals(left[k], right[k]) for k in left)
    return False


def to_plain(value: Any) -> Any:
    """Convert a Rex value into something json.dumps can serialise."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [to_plain(v) for v in value]
    if isinstance(value, dict):
        return {str(k): to_plain(v) for k, v in value.items()}
    if isinstance(value, RexFunction):
        return "<function %s>" % value.name
    if isinstance(value, Builtin):
        return "<builtin %s>" % value.name
    return repr(value)
