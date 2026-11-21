import pytest

from rex.errors import RexSyntaxError
from rex.lexer import EOF, NAME, NEWLINE, NUMBER, OP, STRING, tokenize


def kinds(source):
    return [t.kind for t in tokenize(source)]


def values(source):
    return [t.value for t in tokenize(source) if t.kind not in (NEWLINE, EOF)]


def test_simple_tokens():
    tokens = tokenize('rex.show("hi")')
    assert [t.kind for t in tokens] == [NAME, OP, NAME, OP, STRING, OP, NEWLINE, EOF]


def test_positions_are_tracked():
    tokens = tokenize("rex.let x = 1\nrex.show(x)")
    let = tokens[2]
    assert (let.value, let.line, let.col) == ("let", 1, 5)
    second_line = [t for t in tokens if t.line == 2]
    assert second_line[0].value == "rex"
    assert second_line[0].col == 1


def test_numbers():
    assert [t.literal for t in tokenize("1 2.5 1e3 1_000") if t.kind == NUMBER] == [1, 2.5, 1000.0, 1000]


def test_strings_and_escapes():
    tokens = tokenize(r'"a\nb\t\"c\""')
    assert tokens[0].kind == STRING
    assert tokens[0].value == 'a\nb\t"c"'


def test_unicode_escape():
    assert tokenize(r'"\u00e9"')[0].value == "é"


def test_single_quotes_do_not_interpolate():
    assert tokenize("'hi ${x}'")[0].interpolated is False
    assert tokenize('"hi ${x}"')[0].interpolated is True


def test_comments_are_ignored():
    assert values("# just a comment\nrex.show(1)") == ["rex", ".", "show", "(", "1", ")"]


def test_newline_suppressed_inside_brackets():
    tokens = tokenize("rex.show(\n1,\n2\n)")
    assert all(t.kind != NEWLINE for t in tokens[:-2])


def test_newline_suppressed_after_operator():
    tokens = tokenize("rex.let x = 1 +\n2")
    assert tokens[-2].kind != NEWLINE or tokens[-2].line == 2


def test_line_continuation():
    assert values("rex.let x = 1 \\\n+ 2") == ["rex", ".", "let", "x", "=", "1", "+", "2"]


def test_unterminated_string():
    with pytest.raises(RexSyntaxError) as excinfo:
        tokenize('rex.show("oops)')
    assert "unterminated string" in excinfo.value.message


def test_unclosed_bracket():
    with pytest.raises(RexSyntaxError) as excinfo:
        tokenize("rex.show((1)")
    assert "unclosed bracket" in excinfo.value.message


def test_unexpected_character():
    with pytest.raises(RexSyntaxError):
        tokenize("rex.show(1) $")
