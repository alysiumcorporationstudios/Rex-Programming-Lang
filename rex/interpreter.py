"""Tree walking interpreter for Rex."""

from __future__ import annotations

import difflib
import os
import sys
from typing import Any, Dict, List, Optional, TextIO

from . import ast_nodes as ast
from .builtins import make_stdlib
from .errors import (
    BreakSignal,
    ContinueSignal,
    ExitSignal,
    ReturnSignal,
    RexError,
    RexImportError,
    RexRuntimeError,
)
from .parser import parse
from .values import (
    Builtin,
    RexFunction,
    describe_type,
    equals,
    format_value,
    truthy,
)

DEFAULT_MAX_STEPS = 5_000_000
DEFAULT_MAX_DEPTH = 200


class Scope:
    """A lexical scope. Scopes form a chain that ends at the global scope."""

    __slots__ = ("vars", "parent", "imported")

    def __init__(self, parent: Optional["Scope"] = None) -> None:
        self.vars: Dict[str, Any] = {}
        self.parent = parent
        self.imported = False

    def declare(self, name: str, value: Any) -> None:
        self.vars[name] = value

    def lookup(self, name: str):
        scope: Optional[Scope] = self
        while scope is not None:
            if name in scope.vars:
                return True, scope.vars[name]
            scope = scope.parent
        return False, None

    def assign(self, name: str, value: Any) -> bool:
        scope: Optional[Scope] = self
        while scope is not None:
            if name in scope.vars:
                scope.vars[name] = value
                return True
            scope = scope.parent
        return False

    def visible_names(self) -> List[str]:
        names: List[str] = []
        scope: Optional[Scope] = self
        while scope is not None:
            names.extend(scope.vars.keys())
            scope = scope.parent
        return names


class RexInterpreter:
    """Runs Rex programs.

    >>> interp = RexInterpreter()
    >>> interp.run_source('rex.show("Sawubona")')
    ['Sawubona']
    """

    def __init__(
        self,
        stdout: Optional[TextIO] = None,
        argv: Optional[List[str]] = None,
        max_steps: int = DEFAULT_MAX_STEPS,
        max_depth: int = DEFAULT_MAX_DEPTH,
        cwd: Optional[str] = None,
    ) -> None:
        from . import __version__

        self.version = __version__
        self.stdout = stdout if stdout is not None else sys.stdout
        self.argv = list(argv or [])
        self.max_steps = max_steps
        self.max_depth = max_depth
        self.cwd = cwd or os.getcwd()
        self.output: List[str] = []
        self.exit_code = 0
        self.steps = 0
        self.depth = 0
        self.globals = Scope()
        self.rex = make_stdlib(self)
        self.globals.vars["rex"] = self.rex
        self._file_stack: List[Any] = [("<input>", "")]
        self._import_stack: List[str] = []

    # -- output -----------------------------------------------------------

    def write(self, text: str) -> None:
        self.output.append(text)
        try:
            self.stdout.write(text + "\n")
            self.stdout.flush()
        except (BrokenPipeError, ValueError):  # pragma: no cover - closed pipe
            pass

    # -- public API -------------------------------------------------------

    def run_source(self, source: str, filename: str = "<input>", reset: bool = True) -> List[str]:
        """Parse and run Rex source, returning everything `rex.show` printed."""
        if reset:
            self.reset()
        self._file_stack = [(filename, source)]
        program = parse(source, filename)
        self._execute(program, self.globals)
        return list(self.output)

    def run_file(self, path: str) -> List[str]:
        """Read a `.rex` file and run it."""
        try:
            with open(path, "r", encoding="utf-8") as handle:
                source = handle.read()
        except FileNotFoundError:
            raise RexImportError("file not found: %s" % path) from None
        except OSError as exc:
            raise RexImportError("cannot read %s: %s" % (path, exc)) from None
        return self.run_source(source, filename=path)

    def reset(self) -> None:
        self.output = []
        self.steps = 0
        self.depth = 0
        self.exit_code = 0
        self.globals = Scope()
        self.globals.vars["rex"] = self.rex
        self._import_stack = []

    # -- helpers ----------------------------------------------------------

    @property
    def _current(self):
        return self._file_stack[-1]

    def _error(self, message: str, node: Any = None, hint: Optional[str] = None) -> RexRuntimeError:
        filename, source = self._current
        line = getattr(node, "line", None)
        col = getattr(node, "col", None)
        return RexRuntimeError(
            message, line=line, col=col, filename=filename, source=source, hint=hint
        )

    def _tick(self, node: Any) -> None:
        self.steps += 1
        if self.steps > self.max_steps:
            raise self._error(
                "execution limit reached (%d steps)" % self.max_steps,
                node,
                hint="check for an infinite loop, or raise --max-steps",
            )

    # -- statements -------------------------------------------------------

    def _execute(self, program: ast.Program, scope: Scope) -> None:
        try:
            self._exec_block(program.body, scope)
        except ReturnSignal:
            return
        except ExitSignal as signal:
            self.exit_code = signal.code

    def _exec_block(self, body: List[ast.Node], scope: Scope) -> None:
        for stmt in body:
            self._exec(stmt, scope)

    def _exec(self, node: ast.Node, scope: Scope) -> None:
        self._tick(node)

        if isinstance(node, ast.ExprStmt):
            self._eval(node.expr, scope)
            return

        if isinstance(node, ast.LetStmt):
            value = self._eval(node.expr, scope)
            scope.declare(node.name, value)
            return

        if isinstance(node, ast.AssignStmt):
            value = self._eval(node.expr, scope)
            self._assign(node.target, value, scope, node)
            return

        if isinstance(node, ast.IfStmt):
            for cond, body in node.branches:
                if truthy(self._eval(cond, scope)):
                    self._exec_block(body, Scope(scope))
                    return
            if node.orelse is not None:
                self._exec_block(node.orelse, Scope(scope))
            return

        if isinstance(node, ast.WhileStmt):
            while truthy(self._eval(node.cond, scope)):
                self._tick(node)
                try:
                    self._exec_block(node.body, Scope(scope))
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return

        if isinstance(node, ast.ForStmt):
            iterable = self._eval(node.iterable, scope)
            items = self._iterate(iterable, node)
            for item in items:
                self._tick(node)
                loop_scope = Scope(scope)
                loop_scope.declare(node.name, item)
                try:
                    self._exec_block(node.body, loop_scope)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
            return

        if isinstance(node, ast.FuncDecl):
            fn = RexFunction(
                name=node.name,
                params=node.params,
                body=node.body,
                closure=scope,
                filename=self._current[0],
                source=self._current[1],
                line=node.line,
            )
            scope.declare(node.name, fn)
            return

        if isinstance(node, ast.ReturnStmt):
            raise ReturnSignal(self._eval(node.expr, scope) if node.expr is not None else None)

        if isinstance(node, ast.BreakStmt):
            raise BreakSignal()

        if isinstance(node, ast.ContinueStmt):
            raise ContinueSignal()

        if isinstance(node, ast.TryStmt):
            try:
                self._exec_block(node.body, Scope(scope))
            except (ReturnSignal, BreakSignal, ContinueSignal, ExitSignal):
                raise
            except RexError as exc:
                handler_scope = Scope(scope)
                handler_scope.declare(
                    node.err_name,
                    {
                        "message": exc.message,
                        "type": type(exc).__name__,
                        "line": exc.line,
                        "col": exc.col,
                        "filename": exc.filename,
                    },
                )
                self._exec_block(node.handler, handler_scope)
            return

        if isinstance(node, ast.ThrowStmt):
            value = self._eval(node.expr, scope)
            if isinstance(value, dict) and "message" in value:
                message = format_value(value.get("message"))
            else:
                message = format_value(value)
            raise self._error(message, node)

        if isinstance(node, ast.ImportStmt):
            path = self._eval(node.expr, scope)
            if not isinstance(path, str):
                raise self._error("rex.import expects a string path, got %s" % describe_type(path), node)
            self._import(path, scope, node)
            return

        if isinstance(node, ast.PassStmt):
            return

        raise self._error("cannot execute %s" % type(node).__name__, node)

    def _assign(self, target: ast.Node, value: Any, scope: Scope, node: ast.Node) -> None:
        if isinstance(target, ast.Var):
            if not scope.assign(target.name, value):
                if scope.imported:
                    scope.declare(target.name, value)
                    return
                raise self._error(
                    "cannot assign to undefined variable '%s'" % target.name,
                    target,
                    hint="declare it first with rex.let %s = ..." % target.name,
                )
            return
        if isinstance(target, ast.GetProp):
            container = self._eval(target.obj, scope)
            if not isinstance(container, dict):
                raise self._error(
                    "cannot set property '%s' on a %s" % (target.name, describe_type(container)), target
                )
            container[target.name] = value
            return
        if isinstance(target, ast.GetIndex):
            container = self._eval(target.obj, scope)
            index = self._eval(target.index, scope)
            if isinstance(container, list):
                if isinstance(index, bool) or not isinstance(index, int):
                    raise self._error("list index must be a number, got %s" % describe_type(index), target)
                if not -len(container) <= index < len(container):
                    raise self._error(
                        "list index %d is out of range for a list of %d item(s)" % (index, len(container)),
                        target,
                    )
                container[index] = value
                return
            if isinstance(container, dict):
                container[str(index)] = value
                return
            raise self._error("cannot index-assign into a %s" % describe_type(container), target)
        raise self._error("cannot assign to this expression", node)

    def _iterate(self, value: Any, node: ast.Node) -> List[Any]:
        if isinstance(value, list):
            return list(value)
        if isinstance(value, str):
            return list(value)
        if isinstance(value, dict):
            return list(value.keys())
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            raise self._error(
                "cannot loop over a number", node,
                hint="use rex.range(0, %s)" % format_value(value),
            )
        raise self._error("cannot loop over a %s" % describe_type(value), node)

    def _import(self, path: str, scope: Scope, node: ast.Node) -> None:
        filename, _ = self._current
        candidates: List[str] = []
        if os.path.isabs(path):
            candidates.append(path)
        else:
            base = os.path.dirname(os.path.abspath(filename)) if filename not in ("<input>", "<stdin>") else self.cwd
            candidates.append(os.path.join(base, path))
            candidates.append(os.path.join(self.cwd, path))
        resolved = next((c for c in candidates if os.path.isfile(c)), None)
        if resolved is None:
            raise RexImportError(
                "cannot import %r: file not found" % path,
                line=node.line, col=node.col, filename=filename, source=self._current[1],
                hint="tried: " + ", ".join(candidates),
            )
        real = os.path.realpath(resolved)
        if real in self._import_stack:
            raise RexImportError(
                "circular import detected: %s" % path,
                line=node.line, col=node.col, filename=filename, source=self._current[1],
            )
        try:
            with open(real, "r", encoding="utf-8") as handle:
                source = handle.read()
        except OSError as exc:
            raise RexImportError("cannot read %s: %s" % (path, exc)) from None
        program = parse(source, resolved)
        self._import_stack.append(real)
        self._file_stack.append((resolved, source))
        try:
            self._exec_block(program.body, scope)
        finally:
            self._file_stack.pop()
            self._import_stack.pop()
        scope.imported = True

    # -- expressions ------------------------------------------------------

    def _eval(self, node: Optional[ast.Node], scope: Scope) -> Any:
        if node is None:
            return None

        if isinstance(node, ast.Literal):
            return node.value

        if isinstance(node, ast.Var):
            found, value = scope.lookup(node.name)
            if found:
                return value
            names = scope.visible_names()
            suggestion = difflib.get_close_matches(node.name, names, n=1)
            hint = None
            if suggestion:
                hint = "did you mean '%s'?" % suggestion[0]
            raise self._error("undefined variable '%s'" % node.name, node, hint)

        if isinstance(node, ast.Interp):
            out: List[str] = []
            for part in node.parts:
                if isinstance(part, str):
                    out.append(part)
                else:
                    out.append(format_value(self._eval(part, scope)))
            return "".join(out)

        if isinstance(node, ast.ListLit):
            return [self._eval(item, scope) for item in node.items]

        if isinstance(node, ast.DictLit):
            result: Dict[str, Any] = {}
            for key_node, value_node in node.pairs:
                key = self._eval(key_node, scope)
                if isinstance(key, bool) or not isinstance(key, (str, int, float)):
                    raise self._error(
                        "dictionary keys must be strings or numbers, got %s" % describe_type(key), key_node
                    )
                result[str(key)] = self._eval(value_node, scope)
            return result

        if isinstance(node, ast.Unary):
            value = self._eval(node.operand, scope)
            if node.op == "-":
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise self._error("cannot negate a %s" % describe_type(value), node)
                return -value
            if node.op == "not":
                return not truthy(value)
            raise self._error("unknown unary operator %r" % node.op, node)

        if isinstance(node, ast.Logical):
            left = self._eval(node.left, scope)
            if node.op == "and":
                return self._eval(node.right, scope) if truthy(left) else left
            return left if truthy(left) else self._eval(node.right, scope)

        if isinstance(node, ast.Binary):
            return self._binary(node, scope)

        if isinstance(node, ast.Call):
            callee = self._eval(node.callee, scope)
            args = [self._eval(arg, scope) for arg in node.args]
            return self._call(callee, args, node)

        if isinstance(node, ast.GetProp):
            container = self._eval(node.obj, scope)
            if isinstance(container, dict):
                if node.name in container:
                    return container[node.name]
                available = list(container.keys())[:8]
                hint = None
                if available:
                    hint = "available keys: " + ", ".join(repr(k) for k in available)
                raise self._error("key '%s' not found" % node.name, node, hint)
            if isinstance(container, (list, str)):
                raise self._error(
                    "a %s has no properties (tried '.%s')" % (describe_type(container), node.name),
                    node,
                    hint="use rex.len(x), x[0] or rex.json.stringify(x)",
                )
            raise self._error(
                "cannot read property '%s' of a %s" % (node.name, describe_type(container)), node
            )

        if isinstance(node, ast.GetIndex):
            container = self._eval(node.obj, scope)
            index = self._eval(node.index, scope)
            return self._index(container, index, node)

        raise self._error("cannot evaluate %s" % type(node).__name__, node)

    def _index(self, container: Any, index: Any, node: ast.Node) -> Any:
        if isinstance(container, list):
            if isinstance(index, bool) or not isinstance(index, int):
                raise self._error("list index must be a number, got %s" % describe_type(index), node)
            if not -len(container) <= index < len(container):
                raise self._error(
                    "list index %d is out of range for a list of %d item(s)" % (index, len(container)),
                    node,
                    hint="Rex indexes start at 0",
                )
            return container[index]
        if isinstance(container, str):
            if isinstance(index, bool) or not isinstance(index, int):
                raise self._error("string index must be a number, got %s" % describe_type(index), node)
            if not -len(container) <= index < len(container):
                raise self._error("string index %d is out of range" % index, node)
            return container[index]
        if isinstance(container, dict):
            key = str(index) if not isinstance(index, str) else index
            if key in container:
                return container[key]
            raise self._error("key '%s' not found" % key, node)
        raise self._error("cannot index into a %s" % describe_type(container), node)

    def _binary(self, node: ast.Binary, scope: Scope) -> Any:
        op = node.op
        left = self._eval(node.left, scope)
        right = self._eval(node.right, scope)

        if op in ("==", "!="):
            result = equals(left, right)
            return result if op == "==" else not result

        if op in ("<", "<=", ">", ">="):
            left_num = isinstance(left, (int, float)) and not isinstance(left, bool)
            right_num = isinstance(right, (int, float)) and not isinstance(right, bool)
            if not ((left_num and right_num) or (isinstance(left, str) and isinstance(right, str))):
                raise self._error(
                    "cannot compare %s and %s with '%s'" % (describe_type(left), describe_type(right), op),
                    node,
                )
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            return left >= right

        if op == "+":
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, list) and isinstance(right, list):
                return left + right
            if _is_number(left) and _is_number(right):
                return left + right
            raise self._error(
                "cannot add %s and %s" % (describe_type(left), describe_type(right)),
                node,
                hint='join text with rex.str() or "text ${value}" interpolation',
            )

        if op in ("-", "*", "/", "%"):
            if op == "*":
                if isinstance(left, str) and _is_int(right):
                    return left * max(0, right)
                if isinstance(left, list) and _is_int(right):
                    return left * max(0, right)
                if isinstance(right, str) and _is_int(left):
                    return right * max(0, left)
            if not (_is_number(left) and _is_number(right)):
                raise self._error(
                    "cannot apply '%s' to %s and %s" % (op, describe_type(left), describe_type(right)), node
                )
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise self._error("division by zero", node)
                return left / right
            if right == 0:
                raise self._error("modulo by zero", node)
            return left % right

        raise self._error("unknown operator %r" % op, node)

    def _call(self, callee: Any, args: List[Any], node: ast.Call) -> Any:
        if isinstance(callee, Builtin):
            return callee.call(args, node.line, node.col, self._current[1], self._current[0])

        if isinstance(callee, RexFunction):
            return self._call_function(callee, args, node)

        raise self._error(
            "cannot call a %s" % describe_type(callee),
            node,
            hint="only functions and builtins can be called",
        )

    def _call_function(self, fn: RexFunction, args: List[Any], node: ast.Node) -> Any:
        params = fn.params
        required = sum(1 for _, default in params if default is None)
        if len(args) > len(params):
            raise self._error(
                "%s() expects at most %d argument(s), got %d" % (fn.name, len(params), len(args)), node
            )
        if len(args) < required:
            raise self._error(
                "%s() expects at least %d argument(s), got %d" % (fn.name, required, len(args)), node
            )
        self.depth += 1
        if self.depth > self.max_depth:
            self.depth -= 1
            raise self._error(
                "maximum call depth (%d) exceeded" % self.max_depth,
                node,
                hint="check for recursion without a base case",
            )
        call_scope = Scope(fn.closure)
        try:
            for index, (name, default) in enumerate(params):
                if index < len(args):
                    call_scope.declare(name, args[index])
                elif default is not None:
                    call_scope.declare(name, self._eval(default, fn.closure))
                else:  # pragma: no cover - guarded by the arity checks above
                    call_scope.declare(name, None)
            try:
                self._exec_block(fn.body, call_scope)
            except ReturnSignal as signal:
                return signal.value
            return None
        finally:
            self.depth -= 1


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def run(source: str, filename: str = "<input>", **kwargs: Any) -> List[str]:
    """Convenience wrapper: run Rex source and return what it printed."""
    return RexInterpreter(**kwargs).run_source(source, filename)
