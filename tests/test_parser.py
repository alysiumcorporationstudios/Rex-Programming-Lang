import pytest

from rex import ast_nodes as ast
from rex.errors import RexSyntaxError
from rex.parser import parse, parse_expression


def test_program_structure():
    program = parse('rex.show("hi")\nrex.let x = 1')
    assert isinstance(program, ast.Program)
    assert len(program.body) == 2
    assert isinstance(program.body[1], ast.LetStmt)
    assert program.body[1].name == "x"


def test_precedence():
    expr = parse_expression("1 + 2 * 3")
    assert isinstance(expr, ast.Binary) and expr.op == "+"
    assert expr.right.op == "*"


def test_comparison_and_logic():
    expr = parse_expression("a > 1 and b < 2")
    assert isinstance(expr, ast.Logical) and expr.op == "and"
    assert expr.left.op == ">"


def test_not_binds_looser_than_comparison():
    expr = parse_expression("not a == b")
    assert isinstance(expr, ast.Unary) and expr.op == "not"
    assert expr.operand.op == "=="


def test_unary_minus():
    expr = parse_expression("-x + 1")
    assert expr.op == "+"
    assert expr.left.op == "-"


def test_if_elif_else():
    program = parse(
        "rex.if a\nrex.show(1)\nrex.elif b\nrex.show(2)\nrex.else\nrex.show(3)\nrex.end"
    )
    node = program.body[0]
    assert isinstance(node, ast.IfStmt)
    assert len(node.branches) == 2
    assert node.orelse is not None


def test_function_with_defaults():
    program = parse("rex.func f(a, b = 2)\nrex.return a\nrex.end")
    fn = program.body[0]
    assert isinstance(fn, ast.FuncDecl)
    assert fn.params[0][0] == "a"
    assert fn.params[1][0] == "b"
    assert isinstance(fn.params[1][1], ast.Literal)


def test_for_loop():
    program = parse("rex.for x in [1,2]\nrex.show(x)\nrex.end")
    node = program.body[0]
    assert isinstance(node, ast.ForStmt) and node.name == "x"


def test_try_catch():
    program = parse("rex.try\nrex.show(1)\nrex.catch e\nrex.show(2)\nrex.end")
    node = program.body[0]
    assert isinstance(node, ast.TryStmt) and node.err_name == "e"


def test_dict_and_list_literals():
    expr = parse_expression('{"a": 1, "b": [1, 2]}')
    assert isinstance(expr, ast.DictLit) and len(expr.pairs) == 2
    assert isinstance(expr.pairs[1][1], ast.ListLit)


def test_assignment_statement():
    program = parse("rex.let x = 1\nx = 2")
    assert isinstance(program.body[1], ast.AssignStmt)
    assert isinstance(program.body[1].target, ast.Var)


def test_index_assignment():
    program = parse('rex.let d = {}\nd["k"] = 1')
    assert isinstance(program.body[1].target, ast.GetIndex)


def test_missing_end():
    with pytest.raises(RexSyntaxError) as excinfo:
        parse("rex.if true\nrex.show(1)")
    assert "rex.end" in excinfo.value.message


def test_unexpected_end():
    with pytest.raises(RexSyntaxError):
        parse("rex.end")


def test_break_outside_loop():
    with pytest.raises(RexSyntaxError) as excinfo:
        parse("rex.break")
    assert "outside of a loop" in excinfo.value.message


def test_break_inside_if_inside_loop_is_fine():
    parse("rex.while true\nrex.if true\nrex.break\nrex.end\nrex.end")


def test_duplicate_parameter():
    with pytest.raises(RexSyntaxError):
        parse("rex.func f(a, a)\nrex.return a\nrex.end")


def test_error_has_position():
    with pytest.raises(RexSyntaxError) as excinfo:
        parse("rex.let = 5", "demo.rex")
    error = excinfo.value
    assert error.line == 1 and error.col == 9
    assert error.filename == "demo.rex"
    assert "demo.rex:1:9" in error.render()


def test_interpolation_parts():
    expr = parse_expression('"hello ${name}, ${1 + 2}"')
    assert isinstance(expr, ast.Interp)
    assert len(expr.parts) == 4


def test_nested_call_expression():
    expr = parse_expression('rex.upper(rex.trim(" x "))')
    assert isinstance(expr, ast.Call)
    assert isinstance(expr.args[0], ast.Call)


def test_trailing_comma_in_list():
    expr = parse_expression("[1, 2,]")
    assert len(expr.items) == 2
