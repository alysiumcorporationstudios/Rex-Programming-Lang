from rex.analyzer import analyze


def messages(source):
    return [(f.level, f.message) for f in analyze(source, "demo.rex")]


def test_clean_program_has_no_findings():
    assert messages('rex.let x = 1\nrex.show(x)') == []


def test_unknown_builtin_is_an_error():
    findings = analyze('rex.sho("hi")', "demo.rex")
    assert len(findings) == 1
    assert findings[0].level == "error"
    assert "unknown builtin" in findings[0].message


def test_unknown_namespace_member_is_an_error():
    findings = analyze('rex.show(rex.json.nope("{}"))', "demo.rex")
    assert findings[0].level == "error"


def test_builtin_arity_is_checked():
    findings = analyze("rex.show(rex.len())", "demo.rex")
    assert any("takes 1 argument" in f.message for f in findings)


def test_undefined_variable_is_a_warning():
    findings = analyze("rex.show(nope)", "demo.rex")
    assert findings[0].level == "warning"
    assert "undefined variable" in findings[0].message


def test_function_scope_is_understood():
    source = """
rex.func add(a, b)
  rex.let total = a + b
  rex.return total
rex.end
rex.show(add(1, 2))
"""
    assert messages(source) == []


def test_loop_variable_is_in_scope():
    assert messages("rex.for i in [1,2]\nrex.show(i)\nrex.end") == []


def test_catch_variable_is_in_scope():
    source = "rex.try\nrex.show(1)\nrex.catch err\nrex.show(err.message)\nrex.end"
    assert messages(source) == []


def test_import_relaxes_checks():
    source = 'rex.import "lib.rex"\nrex.show(something_from_lib())'
    assert messages(source) == []


def test_rex_values_are_known():
    assert messages("rex.show(rex.version, rex.args, rex.math.pi)") == []


def test_findings_are_sorted_by_position():
    source = "rex.show(b)\nrex.show(a)"
    findings = analyze(source, "demo.rex")
    assert [f.line for f in findings] == [1, 2]


def test_render_includes_location():
    findings = analyze("rex.show(nope)", "demo.rex")
    assert findings[0].render("demo.rex").startswith("demo.rex:1:10: warning:")
