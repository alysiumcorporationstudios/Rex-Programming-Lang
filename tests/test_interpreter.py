import io

import pytest

from rex.errors import RexError, RexSyntaxError
from rex.interpreter import RexInterpreter


def run(source, filename="<input>", **kwargs):
    return RexInterpreter(**kwargs).run_source(source, filename)


def value(source):
    """Run source and return the last printed line."""
    return run(source)[-1]


# --- basics --------------------------------------------------------------


def test_show_string():
    assert run('rex.show("yebo")') == ["yebo"]


def test_show_multiple_values():
    assert run('rex.show("a", 1, true)') == ["a 1 true"]


def test_show_without_arguments_prints_blank_line():
    assert run("rex.show()") == [""]


def test_show_pretty_prints_objects():
    out = run('rex.show({"a": 1})')[0]
    assert out == '{\n  "a": 1\n}'


def test_comments_and_blank_lines():
    assert run("# hi\n\nrex.show(1)\n# bye") == ["1"]


def test_top_level_return_stops_the_script():
    assert run('rex.show(1)\nrex.return\nrex.show(2)') == ["1"]


# --- values and operators ------------------------------------------------


@pytest.mark.parametrize(
    "source,expected",
    [
        ("rex.show(1 + 2)", "3"),
        ("rex.show(7 - 2)", "5"),
        ("rex.show(3 * 4)", "12"),
        ("rex.show(10 / 4)", "2.5"),
        ("rex.show(10 % 3)", "1"),
        ("rex.show(-5)", "-5"),
        ("rex.show(2 + 3 * 4)", "14"),
        ("rex.show((2 + 3) * 4)", "20"),
        ('rex.show("a" + "b")', "ab"),
        ("rex.show([1] + [2])", "[\n  1,\n  2\n]"),
        ('rex.show("ab" * 2)', "abab"),
    ],
)
def test_arithmetic(source, expected):
    assert value(source) == expected


@pytest.mark.parametrize(
    "source,expected",
    [
        ("rex.show(1 == 1)", "true"),
        ("rex.show(1 != 2)", "true"),
        ("rex.show(2 > 1)", "true"),
        ("rex.show(2 >= 3)", "false"),
        ('rex.show("a" < "b")', "true"),
        ("rex.show(1 == true)", "false"),
        ("rex.show([1,2] == [1,2])", "true"),
        ('rex.show({"a":1} == {"a":1})', "true"),
        ("rex.show(null == null)", "true"),
    ],
)
def test_comparisons(source, expected):
    assert value(source) == expected


def test_logical_operators_short_circuit():
    source = """
rex.func boom()
  rex.throw "should not run"
rex.end
rex.show(false and boom())
rex.show(true or boom())
rex.show(not false)
"""
    assert run(source) == ["false", "true", "true"]


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("0", "false"),
        ("1", "true"),
        ('""', "false"),
        ('"x"', "true"),
        ("[]", "false"),
        ("[0]", "true"),
        ("{}", "false"),
        ("null", "false"),
    ],
)
def test_truthiness(expression, expected):
    assert value("rex.if %s\nrex.show(true)\nrex.else\nrex.show(false)\nrex.end" % expression) == expected


def test_string_interpolation():
    assert value('rex.let n = "Rex"\nrex.show("hi ${n} ${1 + 1}")') == "hi Rex 2"


def test_nested_interpolation_with_braces():
    assert value('rex.show("${rex.json.stringify({\\"a\\": 1})}")') == '{"a": 1}'


def test_escapes_in_strings():
    assert value(r'rex.show("a\nb")') == "a\nb"


# --- variables -----------------------------------------------------------


def test_let_and_reassign():
    assert run("rex.let x = 1\nx = x + 1\nrex.show(x)") == ["2"]


def test_undefined_variable_has_hint():
    with pytest.raises(RexError) as excinfo:
        run("rex.let total = 1\nrex.show(totl)")
    assert "undefined variable 'totl'" in excinfo.value.message
    assert "did you mean 'total'" in (excinfo.value.hint or "")


def test_assign_to_undefined_variable_fails():
    with pytest.raises(RexError):
        run("nope = 1")


def test_property_and_index_assignment():
    source = """
rex.let d = {"a": 1}
d.a = 2
d["b"] = 3
rex.show(d.a, d["b"])
"""
    assert run(source) == ["2 3"]


# --- control flow --------------------------------------------------------


def test_if_elif_else():
    def grade(score):
        return value(
            "rex.let s = %d\nrex.if s >= 90\nrex.show(\"A\")\nrex.elif s >= 75\nrex.show(\"B\")\n"
            "rex.else\nrex.show(\"C\")\nrex.end" % score
        )

    assert grade(95) == "A"
    assert grade(80) == "B"
    assert grade(10) == "C"


def test_while_loop():
    assert run("rex.let i = 0\nrex.while i < 3\ni = i + 1\nrex.show(i)\nrex.end") == ["1", "2", "3"]


def test_for_over_list_string_and_dict():
    assert run("rex.for x in [1,2]\nrex.show(x)\nrex.end") == ["1", "2"]
    assert run('rex.for c in "ab"\nrex.show(c)\nrex.end') == ["a", "b"]
    assert run('rex.for k in {"a": 1}\nrex.show(k)\nrex.end') == ["a"]


def test_for_over_number_has_hint():
    with pytest.raises(RexError) as excinfo:
        run("rex.for i in 5\nrex.show(i)\nrex.end")
    assert "rex.range" in (excinfo.value.hint or "")


def test_break_and_continue():
    source = """
rex.for i in rex.range(0, 10)
  rex.if i == 2
    rex.continue
  rex.end
  rex.if i == 4
    rex.break
  rex.end
  rex.show(i)
rex.end
"""
    assert run(source) == ["0", "1", "3"]


def test_nested_loops_break_only_inner():
    source = """
rex.for a in [1, 2]
  rex.for b in [1, 2]
    rex.break
  rex.end
  rex.show(a)
rex.end
"""
    assert run(source) == ["1", "2"]


def test_infinite_loop_hits_step_limit():
    with pytest.raises(RexError) as excinfo:
        RexInterpreter(max_steps=1000).run_source("rex.while true\nrex.end")
    assert "execution limit" in excinfo.value.message


# --- functions -----------------------------------------------------------


def test_function_call_and_return():
    source = """
rex.func add(a, b)
  rex.return a + b
rex.end
rex.show(add(2, 3))
"""
    assert run(source) == ["5"]


def test_function_without_return_returns_null():
    assert run('rex.func f()\nrex.show("x")\nrex.end\nrex.show(f())') == ["x", "null"]


def test_default_parameters():
    source = """
rex.func greet(name, greeting = "Sawubona")
  rex.return "${greeting} ${name}"
rex.end
rex.show(greet("Rex"))
rex.show(greet("Rex", "Hello"))
"""
    assert run(source) == ["Sawubona Rex", "Hello Rex"]


def test_recursion():
    source = """
rex.func fact(n)
  rex.if n <= 1
    rex.return 1
  rex.end
  rex.return n * fact(n - 1)
rex.end
rex.show(fact(5))
"""
    assert run(source) == ["120"]


def test_closures():
    source = """
rex.func counter()
  rex.let n = 0
  rex.func bump()
    n = n + 1
    rex.return n
  rex.end
  rex.return bump
rex.end
rex.let c = counter()
rex.show(c(), c(), c())
"""
    assert run(source) == ["1 2 3"]


def test_arity_errors():
    with pytest.raises(RexError) as excinfo:
        run("rex.func f(a)\nrex.return a\nrex.end\nrex.show(f(1, 2))")
    assert "at most 1" in excinfo.value.message

    with pytest.raises(RexError) as excinfo:
        run("rex.func f(a)\nrex.return a\nrex.end\nrex.show(f())")
    assert "at least 1" in excinfo.value.message


def test_recursion_limit():
    source = """
rex.func loop(n)
  rex.return loop(n + 1)
rex.end
rex.show(loop(0))
"""
    with pytest.raises(RexError) as excinfo:
        RexInterpreter(max_depth=20).run_source(source)
    assert "call depth" in excinfo.value.message


def test_function_scope_does_not_leak():
    source = """
rex.func f()
  rex.let inner = 1
  rex.return inner
rex.end
rex.show(f())
rex.show(inner)
"""
    with pytest.raises(RexError):
        run(source)


def test_cannot_call_a_non_function():
    with pytest.raises(RexError) as excinfo:
        run("rex.let x = 1\nrex.show(x())")
    assert "cannot call a number" in excinfo.value.message


# --- errors --------------------------------------------------------------


def test_try_catch_binds_error_dict():
    source = """
rex.try
  rex.throw "boom"
rex.catch err
  rex.show(err.message)
rex.end
"""
    assert run(source) == ["boom"]


def test_catch_runtime_errors():
    source = """
rex.try
  rex.show(rex.len(1))
rex.catch err
  rex.show("handled")
rex.end
"""
    assert run(source) == ["handled"]


def test_uncaught_error_propagates():
    with pytest.raises(RexError):
        run('rex.throw "boom"')


def test_error_position_points_at_source():
    with pytest.raises(RexError) as excinfo:
        run("rex.show(1)\nrex.show(missing)", "demo.rex")
    error = excinfo.value
    assert error.line == 2
    assert error.filename == "demo.rex"
    assert "demo.rex:2" in error.render()


def test_division_by_zero():
    with pytest.raises(RexError) as excinfo:
        run("rex.show(1 / 0)")
    assert "division by zero" in excinfo.value.message


def test_cannot_add_string_and_number():
    with pytest.raises(RexError) as excinfo:
        run('rex.show("a" + 1)')
    assert "cannot add string and number" in excinfo.value.message


def test_missing_key_message():
    with pytest.raises(RexError) as excinfo:
        run('rex.let d = {"a": 1}\nrex.show(d.b)')
    assert "key 'b' not found" in excinfo.value.message


def test_index_out_of_range():
    with pytest.raises(RexError):
        run("rex.let l = [1]\nrex.show(l[5])")


def test_syntax_error_is_raised():
    with pytest.raises(RexSyntaxError):
        run("rex.let = 1")


# --- imports -------------------------------------------------------------


def test_import_shares_scope(tmp_path):
    library = tmp_path / "lib.rex"
    library.write_text('rex.func double(n)\nrex.return n * 2\nrex.end\n', encoding="utf-8")
    main = tmp_path / "main.rex"
    main.write_text('rex.import "lib.rex"\nrex.show(double(21))', encoding="utf-8")
    interp = RexInterpreter()
    assert interp.run_file(str(main)) == ["42"]


def test_import_missing_file(tmp_path):
    main = tmp_path / "main.rex"
    main.write_text('rex.import "nope.rex"', encoding="utf-8")
    with pytest.raises(RexError):
        RexInterpreter().run_file(str(main))


def test_circular_import_detected(tmp_path):
    a = tmp_path / "a.rex"
    b = tmp_path / "b.rex"
    a.write_text('rex.import "b.rex"', encoding="utf-8")
    b.write_text('rex.import "a.rex"', encoding="utf-8")
    with pytest.raises(RexError) as excinfo:
        RexInterpreter().run_file(str(a))
    assert "circular import" in excinfo.value.message


# --- interpreter API -----------------------------------------------------


def test_output_is_captured_and_streamed():
    buffer = io.StringIO()
    interp = RexInterpreter(stdout=buffer)
    output = interp.run_source('rex.show("hi")')
    assert output == ["hi"]
    assert buffer.getvalue() == "hi\n"


def test_reset_clears_state():
    interp = RexInterpreter()
    interp.run_source("rex.let x = 1")
    interp.run_source("rex.show(1)")
    assert "x" not in interp.globals.vars


def test_exit_code():
    interp = RexInterpreter()
    interp.run_source("rex.exit(3)")
    assert interp.exit_code == 3


def test_argv_is_exposed():
    interp = RexInterpreter(argv=["one", "two"])
    assert interp.run_source("rex.show(rex.args)") == ['[\n  "one",\n  "two"\n]']
