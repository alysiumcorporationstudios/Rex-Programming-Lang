"""Interactive Read-Eval-Print loop for `rex repl`."""

from __future__ import annotations

from typing import List, Optional

from . import ast_nodes as ast
from .errors import ExitSignal, RexError, RexSyntaxError
from .interpreter import RexInterpreter
from .parser import Parser
from .values import format_value

BANNER = "Rex %s — type :help for commands, Ctrl-D to leave"

HELP = """\
:help          show this help
:vars          list variables defined in this session
:clear         forget every variable
:quit / :q     leave the REPL

Anything else runs as Rex code. Blocks such as rex.if ... rex.end can be
typed over several lines; the prompt switches to '...' until the block closes.
"""


def repl(interp: Optional[RexInterpreter] = None) -> int:
    interp = interp or RexInterpreter()
    from . import __version__

    print(BANNER % __version__)
    buffer: List[str] = []
    while True:
        prompt = "rex> " if not buffer else "...> "
        try:
            line = input(prompt)
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            buffer = []
            print("\n(interrupted)")
            continue

        stripped = line.strip()
        if not buffer and stripped.startswith(":"):
            command = stripped.lower()
            if command in (":quit", ":q", ":exit"):
                return 0
            if command == ":help":
                print(HELP)
                continue
            if command == ":vars":
                names = sorted(interp.globals.vars.keys())
                visible = [n for n in names if n != "rex"]
                if not visible:
                    print("(no variables yet)")
                for name in visible:
                    print("%s = %s" % (name, format_value(interp.globals.vars[name])))
                continue
            if command == ":clear":
                interp.reset()
                print("(cleared)")
                continue
            print("unknown command %r — try :help" % stripped)
            continue

        buffer.append(line)
        source = "\n".join(buffer)
        try:
            program = Parser(source, "<repl>").parse()
        except RexSyntaxError as exc:
            if _is_incomplete(exc):
                continue
            print(exc.render())
            buffer = []
            continue
        buffer = []
        try:
            _run_program(interp, program, source)
        except ExitSignal as signal:
            print("(exit %d)" % signal.code)
            return signal.code
        except RexError as exc:
            print(exc.render())
        except KeyboardInterrupt:
            print("(interrupted)")
    return 0


def _is_incomplete(exc: RexSyntaxError) -> bool:
    message = exc.message
    return (
        "unexpected end of file" in message
        or "unclosed bracket" in message
        or "unterminated string" in message
    )


def _run_program(interp: RexInterpreter, program: ast.Program, source: str) -> None:
    """Execute parsed REPL input, echoing the value of a bare expression."""
    interp._file_stack = [("<repl>", source)]
    if len(program.body) == 1 and isinstance(program.body[0], ast.ExprStmt):
        stmt = program.body[0]
        if not isinstance(stmt.expr, ast.Call):
            value = interp._eval(stmt.expr, interp.globals)
            if value is not None:
                print(format_value(value))
            return
    interp._exec_block(program.body, interp.globals)
