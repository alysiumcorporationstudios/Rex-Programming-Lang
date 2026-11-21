"""Recursive descent parser for Rex.

Grammar (v1.0)::

    program     := statement*
    statement   := let | assign | if | while | for | func | return
                 | break | continue | try | throw | import | pass | expr
    let         := 'rex' '.' 'let' NAME '=' expression
    assign      := assignable '=' expression
    if          := 'rex' '.' 'if' expression block
                   ('rex' '.' 'elif' expression block)*
                   ('rex' '.' 'else' block)? 'rex' '.' 'end'
    while       := 'rex' '.' 'while' expression block 'rex' '.' 'end'
    for         := 'rex' '.' 'for' NAME 'in' expression block 'rex' '.' 'end'
    func        := 'rex' '.' 'func' NAME '(' params? ')' block 'rex' '.' 'end'
    try         := 'rex' '.' 'try' block 'rex' '.' 'catch' NAME block 'rex' '.' 'end'
    expression  := or
    or          := and (('or' | '||') and)*
    and         := not (('and' | '&&') not)*
    not         := ('not' | '!') not | comparison
    comparison  := sum (('==' | '!=' | '<' | '<=' | '>' | '>=') sum)*
    sum         := product (('+' | '-') product)*
    product     := unary (('*' | '/' | '%') unary)*
    unary       := '-' unary | primary
    primary     := NUMBER | STRING | 'true' | 'false' | 'null' | NAME
                 | list | dict | '(' expression ')' | call | index | member
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from . import ast_nodes as ast
from .errors import RexSyntaxError
from .lexer import EOF, NAME, NEWLINE, NUMBER, OP, STRING, Token, describe_token, tokenize

CONTROL_KEYWORDS = {
    "let", "if", "elif", "else", "end", "while", "for", "func",
    "return", "break", "continue", "try", "catch", "throw", "import", "pass",
}

BLOCK_TERMINATORS = {"end", "elif", "else", "catch"}

_COMPARISONS = {"==", "!=", "<", "<=", ">", ">="}


class Parser:
    """Turns Rex source text into an AST."""

    def __init__(self, source: str, filename: str = "<input>") -> None:
        self.source = source
        self.filename = filename
        self.tokens = tokenize(source, filename)
        self.pos = 0
        self.loop_depth = 0
        self.func_depth = 0

    # -- token helpers ----------------------------------------------------

    def peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def advance(self) -> Token:
        tok = self.peek()
        if tok.kind != EOF:
            self.pos += 1
        return tok

    def skip_newlines(self) -> None:
        while self.peek().kind == NEWLINE:
            self.pos += 1

    def error(self, message: str, token: Optional[Token] = None, hint: Optional[str] = None) -> RexSyntaxError:
        tok = token or self.peek()
        return RexSyntaxError(
            message,
            line=tok.line,
            col=tok.col,
            length=max(1, tok.length),
            filename=self.filename,
            source=self.source,
            hint=hint,
        )

    def expect_op(self, value: str, context: str) -> Token:
        self.skip_newlines()
        tok = self.peek()
        if tok.kind != OP or tok.value != value:
            raise self.error(
                "expected %r %s, found %s" % (value, context, describe_token(tok)),
                tok,
            )
        return self.advance()

    def expect_name(self, context: str) -> Token:
        self.skip_newlines()
        tok = self.peek()
        if tok.kind != NAME:
            raise self.error("expected a name %s, found %s" % (context, describe_token(tok)), tok)
        return self.advance()

    def is_control_start(self, keyword: str) -> bool:
        """True when the cursor sits on `rex . <keyword>`."""
        a, b, c = self.peek(), self.peek(1), self.peek(2)
        return (
            a.kind == NAME and a.value == "rex"
            and b.kind == OP and b.value == "."
            and c.kind == NAME and c.value == keyword
        )

    def at_control_keyword(self) -> Optional[str]:
        a, b, c = self.peek(), self.peek(1), self.peek(2)
        if (
            a.kind == NAME and a.value == "rex"
            and b.kind == OP and b.value == "."
            and c.kind == NAME and c.value in CONTROL_KEYWORDS
        ):
            return c.value
        return None

    def consume_control(self, keyword: str) -> Token:
        self.advance()  # rex
        self.advance()  # .
        tok = self.advance()  # keyword
        if tok.value != keyword:  # pragma: no cover - guarded by caller
            raise self.error("expected 'rex.%s'" % keyword, tok)
        return tok

    # -- entry point ------------------------------------------------------

    def parse(self) -> ast.Program:
        self.skip_newlines()
        body: List[ast.Node] = []
        while self.peek().kind != EOF:
            body.append(self.parse_statement())
            self.skip_newlines()
        program = ast.Program(body=body)
        program.line = 1
        program.col = 1
        return program

    def parse_expression_only(self) -> ast.Node:
        self.skip_newlines()
        expr = self.parse_expression()
        self.skip_newlines()
        if self.peek().kind != EOF:
            raise self.error("unexpected %s after expression" % describe_token(self.peek()))
        return expr

    # -- statements -------------------------------------------------------

    def parse_statement(self) -> ast.Node:
        self.skip_newlines()
        tok = self.peek()
        if tok.kind == EOF:
            raise self.error("unexpected end of file, expected a statement")

        keyword = self.at_control_keyword()
        if keyword is not None:
            if keyword in BLOCK_TERMINATORS:
                raise self.error(
                    "unexpected 'rex.%s' without a matching block" % keyword,
                    tok,
                    hint="check that every rex.if / rex.while / rex.for / rex.func / rex.try is closed with rex.end",
                )
            if keyword == "let":
                return self.parse_let()
            if keyword == "if":
                return self.parse_if()
            if keyword == "while":
                return self.parse_while()
            if keyword == "for":
                return self.parse_for()
            if keyword == "func":
                return self.parse_func()
            if keyword == "return":
                return self.parse_return()
            if keyword == "break":
                self.consume_control("break")
                if self.loop_depth == 0:
                    raise self.error("rex.break used outside of a loop", tok)
                node = ast.BreakStmt(tok.line, tok.col)
                return node
            if keyword == "continue":
                self.consume_control("continue")
                if self.loop_depth == 0:
                    raise self.error("rex.continue used outside of a loop", tok)
                return ast.ContinueStmt(tok.line, tok.col)
            if keyword == "try":
                return self.parse_try()
            if keyword == "throw":
                return self.parse_throw()
            if keyword == "import":
                return self.parse_import()
            if keyword == "pass":
                self.consume_control("pass")
                return ast.PassStmt(tok.line, tok.col)

        expr = self.parse_expression()
        self.skip_newlines()
        if self.peek().kind == OP and self.peek().value == "=":
            eq = self.advance()
            if not isinstance(expr, (ast.Var, ast.GetProp, ast.GetIndex)):
                raise self.error("cannot assign to this expression", eq, hint="assign to a variable, a property or an index")
            self.skip_newlines()
            value = self.parse_expression()
            node = ast.AssignStmt(expr.line, expr.col)
            node.target = expr
            node.expr = value
            return node
        stmt = ast.ExprStmt(expr.line, expr.col)
        stmt.expr = expr
        return stmt

    def parse_let(self) -> ast.Node:
        tok = self.consume_control("let")
        self.skip_newlines()
        name_tok = self.expect_name("after 'rex.let'")
        self.expect_op("=", "after the variable name")
        self.skip_newlines()
        value = self.parse_expression()
        node = ast.LetStmt(tok.line, tok.col)
        node.name = name_tok.value
        node.expr = value
        return node

    def parse_return(self) -> ast.Node:
        tok = self.consume_control("return")
        self.skip_newlines()
        nxt = self.peek()
        node = ast.ReturnStmt(tok.line, tok.col)
        if nxt.kind == NEWLINE or nxt.kind == EOF:
            node.expr = None
            return node
        if nxt.kind == NAME and nxt.value == "rex" and self.peek(1).kind == OP and self.peek(1).value == ".":
            node.expr = None
            return node
        node.expr = self.parse_expression()
        return node

    def parse_if(self) -> ast.Node:
        tok = self.consume_control("if")
        cond = self.parse_expression()
        body, terminator = self.parse_block()
        node = ast.IfStmt(tok.line, tok.col)
        node.branches = [(cond, body)]
        node.orelse = None
        while terminator == "elif":
            self.consume_control("elif")
            elif_cond = self.parse_expression()
            elif_body, terminator = self.parse_block()
            node.branches.append((elif_cond, elif_body))
        if terminator == "else":
            self.consume_control("else")
            else_body, terminator = self.parse_block()
            node.orelse = else_body
        if terminator != "end":
            raise self.error("expected 'rex.end' to close 'rex.if'", hint="every rex.if needs a matching rex.end")
        self.consume_control("end")
        return node

    def parse_while(self) -> ast.Node:
        tok = self.consume_control("while")
        cond = self.parse_expression()
        self.loop_depth += 1
        try:
            body, terminator = self.parse_block()
        finally:
            self.loop_depth -= 1
        if terminator != "end":
            raise self.error("expected 'rex.end' to close 'rex.while'")
        self.consume_control("end")
        node = ast.WhileStmt(tok.line, tok.col)
        node.cond = cond
        node.body = body
        return node

    def parse_for(self) -> ast.Node:
        tok = self.consume_control("for")
        self.skip_newlines()
        name_tok = self.expect_name("after 'rex.for'")
        self.skip_newlines()
        in_tok = self.peek()
        if not (in_tok.kind == NAME and in_tok.value == "in"):
            raise self.error("expected 'in' after the loop variable, found %s" % describe_token(in_tok), in_tok)
        self.advance()
        iterable = self.parse_expression()
        self.loop_depth += 1
        try:
            body, terminator = self.parse_block()
        finally:
            self.loop_depth -= 1
        if terminator != "end":
            raise self.error("expected 'rex.end' to close 'rex.for'")
        self.consume_control("end")
        node = ast.ForStmt(tok.line, tok.col)
        node.name = name_tok.value
        node.iterable = iterable
        node.body = body
        return node

    def parse_func(self) -> ast.Node:
        tok = self.consume_control("func")
        self.skip_newlines()
        name_tok = self.expect_name("after 'rex.func'")
        self.expect_op("(", "after the function name")
        params: List[Tuple[str, Optional[ast.Node]]] = []
        seen = set()
        self.skip_newlines()
        if not (self.peek().kind == OP and self.peek().value == ")"):
            while True:
                self.skip_newlines()
                p_tok = self.expect_name("as a parameter name")
                if p_tok.value in seen:
                    raise self.error("duplicate parameter %r" % p_tok.value, p_tok)
                seen.add(p_tok.value)
                default = None
                self.skip_newlines()
                if self.peek().kind == OP and self.peek().value == "=":
                    self.advance()
                    self.skip_newlines()
                    default = self.parse_expression()
                params.append((p_tok.value, default))
                self.skip_newlines()
                if self.peek().kind == OP and self.peek().value == ",":
                    self.advance()
                    continue
                break
        self.expect_op(")", "to close the parameter list")
        self.func_depth += 1
        saved_loop = self.loop_depth
        self.loop_depth = 0
        try:
            body, terminator = self.parse_block()
        finally:
            self.func_depth -= 1
            self.loop_depth = saved_loop
        if terminator != "end":
            raise self.error("expected 'rex.end' to close 'rex.func'")
        self.consume_control("end")
        node = ast.FuncDecl(tok.line, tok.col)
        node.name = name_tok.value
        node.params = params
        node.body = body
        return node

    def parse_try(self) -> ast.Node:
        tok = self.consume_control("try")
        body, terminator = self.parse_block()
        if terminator != "catch":
            raise self.error("expected 'rex.catch' after a 'rex.try' block", hint="a rex.try block must be followed by rex.catch <name>")
        self.consume_control("catch")
        self.skip_newlines()
        err_tok = self.expect_name("after 'rex.catch'")
        handler, terminator = self.parse_block()
        if terminator != "end":
            raise self.error("expected 'rex.end' to close 'rex.try'")
        self.consume_control("end")
        node = ast.TryStmt(tok.line, tok.col)
        node.body = body
        node.err_name = err_tok.value
        node.handler = handler
        return node

    def parse_throw(self) -> ast.Node:
        tok = self.consume_control("throw")
        self.skip_newlines()
        node = ast.ThrowStmt(tok.line, tok.col)
        node.expr = self.parse_expression()
        return node

    def parse_import(self) -> ast.Node:
        tok = self.consume_control("import")
        self.skip_newlines()
        node = ast.ImportStmt(tok.line, tok.col)
        node.expr = self.parse_expression()  # type: ignore[attr-defined]
        return node

    def parse_block(self) -> Tuple[List[ast.Node], str]:
        """Parse statements until a block terminator; return (body, terminator)."""
        self.skip_newlines()
        body: List[ast.Node] = []
        while True:
            tok = self.peek()
            if tok.kind == EOF:
                raise self.error(
                    "unexpected end of file, expected 'rex.end'",
                    tok,
                    hint="a block was opened but never closed",
                )
            keyword = self.at_control_keyword()
            if keyword in BLOCK_TERMINATORS:
                return body, keyword
            body.append(self.parse_statement())
            self.skip_newlines()

    # -- expressions ------------------------------------------------------

    def parse_expression(self) -> ast.Node:
        return self.parse_or()

    def parse_or(self) -> ast.Node:
        left = self.parse_and()
        while True:
            self.skip_newlines()
            tok = self.peek()
            if (tok.kind == NAME and tok.value == "or") or (tok.kind == OP and tok.value == "||"):
                self.advance()
                self.skip_newlines()
                right = self.parse_and()
                node = ast.Logical(tok.line, tok.col)
                node.op = "or"
                node.left = left
                node.right = right
                left = node
            else:
                return left

    def parse_and(self) -> ast.Node:
        left = self.parse_not()
        while True:
            self.skip_newlines()
            tok = self.peek()
            if (tok.kind == NAME and tok.value == "and") or (tok.kind == OP and tok.value == "&&"):
                self.advance()
                self.skip_newlines()
                right = self.parse_not()
                node = ast.Logical(tok.line, tok.col)
                node.op = "and"
                node.left = left
                node.right = right
                left = node
            else:
                return left

    def parse_not(self) -> ast.Node:
        self.skip_newlines()
        tok = self.peek()
        if (tok.kind == NAME and tok.value == "not") or (tok.kind == OP and tok.value == "!"):
            self.advance()
            self.skip_newlines()
            operand = self.parse_not()
            node = ast.Unary(tok.line, tok.col)
            node.op = "not"
            node.operand = operand
            return node
        return self.parse_comparison()

    def parse_comparison(self) -> ast.Node:
        left = self.parse_sum()
        while True:
            self.skip_newlines()
            tok = self.peek()
            if tok.kind == OP and tok.value in _COMPARISONS:
                self.advance()
                self.skip_newlines()
                right = self.parse_sum()
                node = ast.Binary(tok.line, tok.col)
                node.op = tok.value
                node.left = left
                node.right = right
                left = node
            else:
                return left

    def parse_sum(self) -> ast.Node:
        left = self.parse_product()
        while True:
            self.skip_newlines()
            tok = self.peek()
            if tok.kind == OP and tok.value in ("+", "-"):
                self.advance()
                self.skip_newlines()
                right = self.parse_product()
                node = ast.Binary(tok.line, tok.col)
                node.op = tok.value
                node.left = left
                node.right = right
                left = node
            else:
                return left

    def parse_product(self) -> ast.Node:
        left = self.parse_unary()
        while True:
            self.skip_newlines()
            tok = self.peek()
            if tok.kind == OP and tok.value in ("*", "/", "%"):
                self.advance()
                self.skip_newlines()
                right = self.parse_unary()
                node = ast.Binary(tok.line, tok.col)
                node.op = tok.value
                node.left = left
                node.right = right
                left = node
            else:
                return left

    def parse_unary(self) -> ast.Node:
        self.skip_newlines()
        tok = self.peek()
        if tok.kind == OP and tok.value == "-":
            self.advance()
            self.skip_newlines()
            operand = self.parse_unary()
            node = ast.Unary(tok.line, tok.col)
            node.op = "-"
            node.operand = operand
            return node
        if tok.kind == OP and tok.value == "+":
            self.advance()
            self.skip_newlines()
            return self.parse_unary()
        return self.parse_postfix()

    def parse_postfix(self) -> ast.Node:
        expr = self.parse_primary()
        while True:
            tok = self.peek()
            if tok.kind == OP and tok.value == "(":
                self.advance()
                args: List[ast.Node] = []
                self.skip_newlines()
                if not (self.peek().kind == OP and self.peek().value == ")"):
                    while True:
                        self.skip_newlines()
                        args.append(self.parse_expression())
                        self.skip_newlines()
                        if self.peek().kind == OP and self.peek().value == ",":
                            self.advance()
                            self.skip_newlines()
                            if self.peek().kind == OP and self.peek().value == ")":
                                break
                            continue
                        break
                self.expect_op(")", "to close the argument list")
                node = ast.Call(tok.line, tok.col)
                node.callee = expr
                node.args = args
                expr = node
                continue
            if tok.kind == OP and tok.value == "[":
                self.advance()
                self.skip_newlines()
                index = self.parse_expression()
                self.expect_op("]", "to close the index")
                node = ast.GetIndex(tok.line, tok.col)
                node.obj = expr
                node.index = index
                expr = node
                continue
            if tok.kind == OP and tok.value == ".":
                # A newline may not appear between '.' and the property name.
                prop_tok = self.peek(1)
                if prop_tok.kind != NAME:
                    raise self.error("expected a property name after '.', found %s" % describe_token(prop_tok), prop_tok)
                self.advance()
                self.advance()
                node = ast.GetProp(tok.line, tok.col)
                node.obj = expr
                node.name = prop_tok.value
                expr = node
                continue
            return expr

    def parse_primary(self) -> ast.Node:
        self.skip_newlines()
        tok = self.peek()

        if tok.kind == NUMBER:
            self.advance()
            return ast.Literal(tok.line, tok.col, tok.literal)

        if tok.kind == STRING:
            self.advance()
            return self._string_node(tok)

        if tok.kind == NAME:
            if tok.value == "true":
                self.advance()
                return ast.Literal(tok.line, tok.col, True)
            if tok.value == "false":
                self.advance()
                return ast.Literal(tok.line, tok.col, False)
            if tok.value == "null":
                self.advance()
                return ast.Literal(tok.line, tok.col, None)
            if tok.value in ("and", "or", "not", "in"):
                raise self.error("expected an expression, found keyword %r" % tok.value, tok)
            self.advance()
            return ast.Var(tok.line, tok.col, tok.value)

        if tok.kind == OP and tok.value == "(":
            self.advance()
            self.skip_newlines()
            expr = self.parse_expression()
            self.expect_op(")", "to close the group")
            return expr

        if tok.kind == OP and tok.value == "[":
            self.advance()
            items: List[ast.Node] = []
            self.skip_newlines()
            if not (self.peek().kind == OP and self.peek().value == "]"):
                while True:
                    self.skip_newlines()
                    items.append(self.parse_expression())
                    self.skip_newlines()
                    if self.peek().kind == OP and self.peek().value == ",":
                        self.advance()
                        self.skip_newlines()
                        if self.peek().kind == OP and self.peek().value == "]":
                            break
                        continue
                    break
            self.expect_op("]", "to close the list")
            return ast.ListLit(tok.line, tok.col, items)

        if tok.kind == OP and tok.value == "{":
            self.advance()
            pairs: List[Tuple[ast.Node, ast.Node]] = []
            self.skip_newlines()
            if not (self.peek().kind == OP and self.peek().value == "}"):
                while True:
                    self.skip_newlines()
                    key_tok = self.peek()
                    if key_tok.kind == NAME:
                        self.advance()
                        key: ast.Node = ast.Literal(key_tok.line, key_tok.col, key_tok.value)
                    elif key_tok.kind == STRING:
                        self.advance()
                        key = ast.Literal(key_tok.line, key_tok.col, key_tok.value)
                    else:
                        key = self.parse_expression()
                    self.expect_op(":", "after a dictionary key")
                    self.skip_newlines()
                    value = self.parse_expression()
                    pairs.append((key, value))
                    self.skip_newlines()
                    if self.peek().kind == OP and self.peek().value == ",":
                        self.advance()
                        self.skip_newlines()
                        if self.peek().kind == OP and self.peek().value == "}":
                            break
                        continue
                    break
            self.expect_op("}", "to close the dictionary")
            return ast.DictLit(tok.line, tok.col, pairs)

        raise self.error("expected an expression, found %s" % describe_token(tok), tok)

    def _string_node(self, tok: Token) -> ast.Node:
        """Build a Literal or an Interp node from a STRING token."""
        raw = tok.value
        if not tok.interpolated or "${" not in raw:
            return ast.Literal(tok.line, tok.col, raw)

        parts: List[object] = []
        buf: List[str] = []
        i = 0
        n = len(raw)
        while i < n:
            if raw.startswith("${", i):
                depth = 1
                j = i + 2
                quote: Optional[str] = None
                while j < n:
                    c = raw[j]
                    if quote:
                        if c == "\\":
                            j += 2
                            continue
                        if c == quote:
                            quote = None
                    elif c in "\"'":
                        quote = c
                    elif c == "{":
                        depth += 1
                    elif c == "}":
                        depth -= 1
                        if depth == 0:
                            break
                    j += 1
                if j >= n:
                    raise self.error("unterminated '${' in string", tok, hint="close the hole with '}'")
                inner = raw[i + 2:j]
                if not inner.strip():
                    raise self.error("empty '${}' in string", tok)
                sub = Parser(inner, self.filename)
                try:
                    sub.skip_newlines()
                    expr = sub.parse_expression()
                    sub.skip_newlines()
                    if sub.peek().kind != EOF:
                        raise sub.error("unexpected %s in '${}'" % describe_token(sub.peek()))
                except RexSyntaxError as exc:
                    raise self.error("invalid expression in string: %s" % exc.message, tok) from None
                if buf:
                    parts.append("".join(buf))
                    buf = []
                parts.append(expr)
                i = j + 1
                continue
            buf.append(raw[i])
            i += 1
        if buf:
            parts.append("".join(buf))
        if len(parts) == 1 and isinstance(parts[0], str):
            return ast.Literal(tok.line, tok.col, parts[0])
        return ast.Interp(tok.line, tok.col, parts)


def parse(source: str, filename: str = "<input>") -> ast.Program:
    """Parse Rex source text into a Program node."""
    return Parser(source, filename).parse()


def parse_expression(source: str, filename: str = "<input>") -> ast.Node:
    """Parse a single expression, used by the REPL and by string interpolation."""
    return Parser(source, filename).parse_expression_only()
