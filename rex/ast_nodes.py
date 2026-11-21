"""AST node definitions for Rex.

Nodes are plain dataclasses. They carry `line`/`col` so runtime errors can point
at the exact token that failed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


@dataclass
class Node:
    line: int = 0
    col: int = 1

    def to_dict(self) -> dict:
        data = {"type": type(self).__name__}
        for key, value in self.__dict__.items():
            if key in ("line", "col"):
                data[key] = value
            else:
                data[key] = _dump(value)
        return data


def _dump(value: Any) -> Any:
    if isinstance(value, Node):
        return value.to_dict()
    if isinstance(value, (list, tuple)):
        return [_dump(v) for v in value]
    if isinstance(value, dict):
        return {k: _dump(v) for k, v in value.items()}
    return value


# --- expressions ---------------------------------------------------------


@dataclass
class Literal(Node):
    value: Any = None


@dataclass
class Var(Node):
    name: str = ""


@dataclass
class Interp(Node):
    """A double quoted string containing `${expr}` holes."""

    parts: List[Any] = field(default_factory=list)  # str | Node


@dataclass
class ListLit(Node):
    items: List[Node] = field(default_factory=list)


@dataclass
class DictLit(Node):
    pairs: List[Tuple[Node, Node]] = field(default_factory=list)


@dataclass
class Unary(Node):
    op: str = ""
    operand: Optional[Node] = None


@dataclass
class Binary(Node):
    op: str = ""
    left: Optional[Node] = None
    right: Optional[Node] = None


@dataclass
class Logical(Node):
    op: str = ""
    left: Optional[Node] = None
    right: Optional[Node] = None


@dataclass
class Call(Node):
    callee: Node = None  # type: ignore[assignment]
    args: List[Node] = field(default_factory=list)


@dataclass
class GetProp(Node):
    obj: Node = None  # type: ignore[assignment]
    name: str = ""


@dataclass
class GetIndex(Node):
    obj: Node = None  # type: ignore[assignment]
    index: Node = None  # type: ignore[assignment]


# --- statements ----------------------------------------------------------


@dataclass
class Program(Node):
    body: List[Node] = field(default_factory=list)


@dataclass
class ExprStmt(Node):
    expr: Optional[Node] = None


@dataclass
class LetStmt(Node):
    name: str = ""
    expr: Optional[Node] = None


@dataclass
class AssignStmt(Node):
    target: Optional[Node] = None
    expr: Optional[Node] = None


@dataclass
class IfStmt(Node):
    branches: List[Tuple[Node, List[Node]]] = field(default_factory=list)
    orelse: Optional[List[Node]] = None


@dataclass
class WhileStmt(Node):
    cond: Optional[Node] = None
    body: List[Node] = field(default_factory=list)


@dataclass
class ForStmt(Node):
    name: str = ""
    iterable: Optional[Node] = None
    body: List[Node] = field(default_factory=list)


@dataclass
class FuncDecl(Node):
    name: str = ""
    params: List[Tuple[str, Optional[Node]]] = field(default_factory=list)
    body: List[Node] = field(default_factory=list)


@dataclass
class ReturnStmt(Node):
    expr: Optional[Node] = None


@dataclass
class BreakStmt(Node):
    pass


@dataclass
class ContinueStmt(Node):
    pass


@dataclass
class TryStmt(Node):
    body: List[Node] = field(default_factory=list)
    err_name: str = "err"
    handler: List[Node] = field(default_factory=list)


@dataclass
class ThrowStmt(Node):
    expr: Optional[Node] = None


@dataclass
class ImportStmt(Node):
    path: str = ""


@dataclass
class PassStmt(Node):
    pass
