"""Static checks for Rex: `rex check` runs these without executing the program.

The analyzer walks the AST with a lightweight scope model and reports:

* unknown `rex.*` builtins (a typo in `rex.sho` is caught before runtime)
* wrong argument counts for builtin calls with literal arguments
* reads of variables that were never declared in scope
* `rex.break` / `rex.continue` outside a loop (the parser already rejects these)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from . import ast_nodes as ast
from .builtins import make_stdlib
from .parser import parse
from .values import Builtin, Namespace


@dataclass
class Finding:
    level: str  # "error" | "warning"
    message: str
    line: int
    col: int

    def render(self, filename: str) -> str:
        return "%s:%d:%d: %s: %s" % (filename, self.line, self.col, self.level, self.message)


class _Stub:
    argv: List[str] = []
    version = "0.0.0"

    def write(self, text: str) -> None:  # pragma: no cover - never used
        pass


def _rex_members() -> Dict[str, Any]:
    """Every name reachable under `rex`, including namespaces and plain values."""
    members: Dict[str, Any] = {}

    def walk(prefix: str, node: Namespace) -> None:
        for key, value in node.items():
            path = "%s.%s" % (prefix, key)
            members[path] = value if isinstance(value, Builtin) else None
            if isinstance(value, Namespace):
                walk(path, value)

    walk("rex", make_stdlib(_Stub()))
    return members


class _ScopeInfo:
    __slots__ = ("names", "parent", "dynamic")

    def __init__(self, parent: Optional["_ScopeInfo"] = None, dynamic: bool = False) -> None:
        self.names: Set[str] = set()
        self.parent = parent
        self.dynamic = dynamic

    def declare(self, name: str) -> None:
        self.names.add(name)

    def known(self, name: str) -> bool:
        scope: Optional[_ScopeInfo] = self
        while scope is not None:
            if scope.dynamic or name in scope.names:
                return True
            scope = scope.parent
        return False

    def mark_dynamic(self) -> None:
        scope: Optional[_ScopeInfo] = self
        while scope is not None:
            scope.dynamic = True
            scope = scope.parent


class Analyzer:
    """Collects findings for one file."""

    def __init__(self, source: str, filename: str = "<input>") -> None:
        self.source = source
        self.filename = filename
        self.findings: List[Finding] = []
        self.builtins = _rex_members()
        self.globals = _ScopeInfo()
        self.globals.declare("rex")

    def run(self) -> List[Finding]:
        program = parse(self.source, self.filename)
        self._block(program.body, self.globals)
        self.findings.sort(key=lambda f: (f.line, f.col))
        return self.findings

    # -- helpers ----------------------------------------------------------

    def _add(self, level: str, message: str, node: Any) -> None:
        self.findings.append(Finding(level, message, getattr(node, "line", 0), getattr(node, "col", 1)))

    def _block(self, body: List[ast.Node], scope: _ScopeInfo) -> None:
        for stmt in body:
            self._stmt(stmt, scope)

    def _stmt(self, node: ast.Node, scope: _ScopeInfo) -> None:
        if isinstance(node, ast.ExprStmt):
            self._expr(node.expr, scope)
            return
        if isinstance(node, ast.LetStmt):
            self._expr(node.expr, scope)
            scope.declare(node.name)
            return
        if isinstance(node, ast.AssignStmt):
            self._expr(node.expr, scope)
            if isinstance(node.target, ast.Var):
                if not scope.known(node.target.name):
                    self._add("warning", "assignment to undeclared variable '%s'" % node.target.name, node.target)
                scope.declare(node.target.name)
            else:
                self._expr(node.target, scope)
            return
        if isinstance(node, ast.IfStmt):
            for cond, body in node.branches:
                self._expr(cond, scope)
                self._block(body, _ScopeInfo(scope))
            if node.orelse is not None:
                self._block(node.orelse, _ScopeInfo(scope))
            return
        if isinstance(node, ast.WhileStmt):
            self._expr(node.cond, scope)
            self._block(node.body, _ScopeInfo(scope))
            return
        if isinstance(node, ast.ForStmt):
            self._expr(node.iterable, scope)
            inner = _ScopeInfo(scope)
            inner.declare(node.name)
            self._block(node.body, inner)
            return
        if isinstance(node, ast.FuncDecl):
            scope.declare(node.name)
            inner = _ScopeInfo(scope)
            for name, default in node.params:
                inner.declare(name)
                if default is not None:
                    self._expr(default, scope)
            self._block(node.body, inner)
            return
        if isinstance(node, ast.ReturnStmt):
            if node.expr is not None:
                self._expr(node.expr, scope)
            return
        if isinstance(node, ast.TryStmt):
            self._block(node.body, _ScopeInfo(scope))
            inner = _ScopeInfo(scope)
            inner.declare(node.err_name)
            self._block(node.handler, inner)
            return
        if isinstance(node, ast.ThrowStmt):
            self._expr(node.expr, scope)
            return
        if isinstance(node, ast.ImportStmt):
            self._expr(getattr(node, "expr", None), scope)
            scope.mark_dynamic()
            return
        if isinstance(node, (ast.BreakStmt, ast.ContinueStmt, ast.PassStmt)):
            return

    def _expr(self, node: Optional[ast.Node], scope: _ScopeInfo) -> None:
        if node is None:
            return
        if isinstance(node, ast.Literal):
            return
        if isinstance(node, ast.Var):
            if not scope.known(node.name):
                self._add("warning", "undefined variable '%s'" % node.name, node)
            return
        if isinstance(node, ast.Interp):
            for part in node.parts:
                if not isinstance(part, str):
                    self._expr(part, scope)
            return
        if isinstance(node, ast.ListLit):
            for item in node.items:
                self._expr(item, scope)
            return
        if isinstance(node, ast.DictLit):
            for key, value in node.pairs:
                self._expr(key, scope)
                self._expr(value, scope)
            return
        if isinstance(node, ast.Unary):
            self._expr(node.operand, scope)
            return
        if isinstance(node, (ast.Binary, ast.Logical)):
            self._expr(node.left, scope)
            self._expr(node.right, scope)
            return
        if isinstance(node, ast.GetIndex):
            self._expr(node.obj, scope)
            self._expr(node.index, scope)
            return
        if isinstance(node, ast.GetProp):
            if isinstance(node.obj, ast.Var) and node.obj.name == "rex":
                path = "rex." + node.name
                if path not in self.builtins:
                    self._add("error", "unknown builtin 'rex.%s'" % node.name, node)
                return
            self._expr(node.obj, scope)
            return
        if isinstance(node, ast.Call):
            self._check_call(node, scope)
            return

    def _builtin_path(self, node: ast.Call) -> Optional[str]:
        callee = node.callee
        parts: List[str] = []
        while isinstance(callee, ast.GetProp):
            parts.append(callee.name)
            callee = callee.obj
        if isinstance(callee, ast.Var) and callee.name == "rex":
            parts.append("rex")
            return ".".join(reversed(parts))
        return None

    def _check_call(self, node: ast.Call, scope: _ScopeInfo) -> None:
        path = self._builtin_path(node)
        if path is not None:
            if path not in self.builtins:
                self._add("error", "unknown builtin '%s'" % path, node)
                for arg in node.args:
                    self._expr(arg, scope)
                return
            builtin = self.builtins.get(path)
            if builtin is None:
                # a namespace or a plain value, not something callable
                self._add("error", "'%s' is not a function" % path, node)
                for arg in node.args:
                    self._expr(arg, scope)
                return
            count = len(node.args)
            if count < builtin.min_args or (builtin.max_args is not None and count > builtin.max_args):
                if builtin.max_args is None:
                    expected = "at least %d" % builtin.min_args
                elif builtin.min_args == builtin.max_args:
                    expected = str(builtin.min_args)
                else:
                    expected = "%d to %d" % (builtin.min_args, builtin.max_args)
                self._add(
                    "error",
                    "%s() takes %s argument(s) but %d given" % (path, expected, count),
                    node,
                )
            for arg in node.args:
                self._expr(arg, scope)
            return
        self._expr(node.callee, scope)
        for arg in node.args:
            self._expr(arg, scope)


def analyze(source: str, filename: str = "<input>") -> List[Finding]:
    """Parse and statically check Rex source."""
    return Analyzer(source, filename).run()
