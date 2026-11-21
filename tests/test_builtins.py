import json

import pytest

import rex.builtins as builtins_module
from rex.errors import RexError
from rex.interpreter import RexInterpreter


def run(source, **kwargs):
    return RexInterpreter(**kwargs).run_source(source)


def value(source):
    return run(source)[-1]


# --- text ----------------------------------------------------------------


def test_text_helpers():
    assert value('rex.show(rex.upper("abc"))') == "ABC"
    assert value('rex.show(rex.lower("ABC"))') == "abc"
    assert value('rex.show(rex.trim("  x  "))') == "x"
    assert value('rex.show(rex.replace("a-b", "-", "+"))') == "a+b"
    assert value('rex.show(rex.starts_with("rex", "re"))') == "true"
    assert value('rex.show(rex.ends_with("rex", "ex"))') == "true"
    assert value('rex.show(rex.repeat("ab", 2))') == "abab"


def test_split_and_join():
    assert value('rex.show(rex.join(rex.split("a,b,c", ","), "-"))') == "a-b-c"
    assert value('rex.show(rex.split("a b"))') == '[\n  "a",\n  "b"\n]'


def test_contains_works_on_strings_lists_dicts():
    assert value('rex.show(rex.contains("hello", "ell"))') == "true"
    assert value('rex.show(rex.contains([1, 2], 2))') == "true"
    assert value('rex.show(rex.contains({"a": 1}, "a"))') == "true"
    assert value('rex.show(rex.contains([1], 9))') == "false"


# --- collections ---------------------------------------------------------


def test_collection_helpers():
    assert value("rex.show(rex.len([1,2,3]))") == "3"
    assert value('rex.show(rex.len("abc"))') == "3"
    assert value('rex.show(rex.first([9,8]))') == "9"
    assert value('rex.show(rex.last([9,8]))') == "8"
    assert value("rex.show(rex.sum([1,2,3]))") == "6"
    assert value("rex.show(rex.unique([1,1,2]))") == '[\n  1,\n  2\n]'
    assert value("rex.show(rex.range(0, 5, 2))") == "[\n  0,\n  2,\n  4\n]"
    assert value("rex.show(rex.sort([3,1,2]))") == "[\n  1,\n  2,\n  3\n]"
    assert value("rex.show(rex.sort([3,1,2], true))") == "[\n  3,\n  2,\n  1\n]"


def test_push_and_pop_mutate_the_list():
    source = """
rex.let l = [1]
rex.push(l, 2, 3)
rex.show(l)
rex.show(rex.pop(l))
rex.show(l)
"""
    assert run(source) == ["[\n  1,\n  2,\n  3\n]", "3", "[\n  1,\n  2\n]"]


def test_pop_from_empty_returns_null():
    assert value("rex.show(rex.pop([]))") == "null"


def test_keys_values_has():
    assert value('rex.show(rex.keys({"a": 1, "b": 2}))') == '[\n  "a",\n  "b"\n]'
    assert value('rex.show(rex.values({"a": 1}))') == "[\n  1\n]"
    assert value('rex.show(rex.has({"a": 1}, "b"))') == "false"


def test_sort_mixed_values_does_not_crash():
    assert value('rex.show(rex.len(rex.sort([3, "a", null, true])))') == "4"


# --- conversion ----------------------------------------------------------


def test_type_names():
    assert value("rex.show(rex.type(null))") == "null"
    assert value("rex.show(rex.type(1))") == "number"
    assert value('rex.show(rex.type("s"))') == "string"
    assert value("rex.show(rex.type([]))") == "list"
    assert value("rex.show(rex.type({}))") == "dict"
    assert value("rex.show(rex.type(rex.show))") == "builtin"


def test_str_num_bool():
    assert value("rex.show(rex.str(12))") == "12"
    assert value('rex.show(rex.num("42"))') == "42"
    assert value('rex.show(rex.num("4.5"))') == "4.5"
    assert value("rex.show(rex.bool(0))") == "false"
    with pytest.raises(RexError):
        run('rex.show(rex.num("abc"))')


def test_clone_is_deep():
    source = """
rex.let a = {"n": [1]}
rex.let b = rex.clone(a)
rex.push(b.n, 2)
rex.show(rex.len(a.n), rex.len(b.n))
"""
    assert run(source) == ["1 2"]


# --- json ----------------------------------------------------------------


def test_json_parse_and_stringify():
    assert value('rex.show(rex.json.parse(\'{"a": 1}\').a)') == "1"
    assert value('rex.show(rex.json.stringify({"a": 1}))') == '{"a": 1}'
    assert value('rex.show(rex.json.stringify({"a": 1}, true))') == '{\n  "a": 1\n}'


def test_json_parse_error_is_clear():
    with pytest.raises(RexError) as excinfo:
        run('rex.show(rex.json.parse("{oops}"))')
    assert "invalid JSON" in excinfo.value.message


def test_json_stringify_handles_functions():
    assert value("rex.func f()\nrex.return 1\nrex.end\nrex.show(rex.json.stringify(f))") == '"<function f>"'


# --- math ----------------------------------------------------------------


def test_math_helpers():
    assert value("rex.show(rex.math.sqrt(9))") == "3"
    assert value("rex.show(rex.math.floor(1.9))") == "1"
    assert value("rex.show(rex.math.ceil(1.1))") == "2"
    assert value("rex.show(rex.math.round(1.2345, 2))") == "1.23"
    assert value("rex.show(rex.math.abs(-4))") == "4"
    assert value("rex.show(rex.math.pow(2, 10))") == "1024"
    assert value("rex.show(rex.math.min([4, 2, 9]))") == "2"
    assert value("rex.show(rex.math.max(4, 2, 9))") == "9"
    assert value("rex.show(rex.type(rex.math.random()))") == "number"


def test_math_sqrt_of_negative():
    with pytest.raises(RexError):
        run("rex.show(rex.math.sqrt(-1))")


# --- time ----------------------------------------------------------------


def test_time_now_is_iso():
    text = value("rex.show(rex.time.now())")
    assert text.endswith("Z") and "T" in text


# --- env -----------------------------------------------------------------


def test_env_lookup(monkeypatch):
    monkeypatch.setenv("REX_TEST_VALUE", "hello")
    assert value('rex.show(rex.env("REX_TEST_VALUE"))') == "hello"
    assert value('rex.show(rex.env("REX_TEST_MISSING", "fallback"))') == "fallback"


# --- files ---------------------------------------------------------------


def test_file_round_trip(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = """
rex.write("note.txt", "one")
rex.append("note.txt", "-two")
rex.show(rex.read("note.txt"))
rex.show(rex.exists("note.txt"))
rex.show(rex.exists("missing.txt"))
rex.show(rex.list_files("."))
"""
    assert run(source) == ["one-two", "true", "false", '[\n  "note.txt"\n]']


def test_read_missing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RexError) as excinfo:
        run('rex.show(rex.read("nope.txt"))')
    assert "file not found" in excinfo.value.message


def test_write_creates_parent_directories(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run('rex.write("nested/dir/file.txt", "x")')
    assert (tmp_path / "nested" / "dir" / "file.txt").read_text() == "x"


# --- assert / error / exit ----------------------------------------------


def test_assert_passes_and_fails():
    assert run("rex.assert(1 == 1)") == []
    with pytest.raises(RexError) as excinfo:
        run('rex.assert(false, "nope")')
    assert excinfo.value.message == "nope"


def test_error_builtin_throws():
    with pytest.raises(RexError):
        run('rex.error("manual failure")')


def test_exit_sets_code():
    interp = RexInterpreter()
    interp.run_source("rex.exit(7)")
    assert interp.exit_code == 7


# --- arity and type errors ----------------------------------------------


def test_builtin_arity_errors():
    with pytest.raises(RexError) as excinfo:
        run("rex.show(rex.len())")
    assert "at least 1" in excinfo.value.message

    with pytest.raises(RexError) as excinfo:
        run('rex.show(rex.upper("a", "b"))')
    assert "1 argument" in excinfo.value.message


def test_builtin_type_errors_are_explicit():
    with pytest.raises(RexError) as excinfo:
        run("rex.show(rex.upper(1))")
    assert "must be a string, got number" in excinfo.value.message


def test_unknown_namespace_member():
    with pytest.raises(RexError):
        run("rex.json.nope(1)")


# --- HTTP (no network) ---------------------------------------------------


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=None, headers=None):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self.headers = headers or {"Content-Type": "application/json"}
        self._payload = payload
        self.text = text if text is not None else json.dumps(payload or {})
        self.url = "https://example.test/x"

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FakeRequests:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, url, timeout=None, **kwargs):
        self.calls.append({"method": method, "url": url, "timeout": timeout, **kwargs})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.fixture
def fake_http(monkeypatch):
    def install(response):
        fake = FakeRequests(response)
        monkeypatch.setattr(builtins_module, "_requests", lambda: fake)
        return fake

    return install


def test_get_returns_parsed_json(fake_http):
    fake = fake_http(FakeResponse(payload={"id": 1, "title": "hi"}))
    assert value('rex.show(rex.get("https://example.test/x").title)') == "hi"
    assert fake.calls[0]["method"] == "GET"
    assert fake.calls[0]["timeout"] == 15


def test_get_options_are_forwarded(fake_http):
    fake = fake_http(FakeResponse(payload={}))
    run('rex.get("https://example.test/x", {"headers": {"X-Test": "1"}, "timeout": 3})')
    assert fake.calls[0]["headers"] == {"X-Test": "1"}
    assert fake.calls[0]["timeout"] == 3


def test_post_sends_json_body(fake_http):
    fake = fake_http(FakeResponse(payload={"id": 2}))
    assert value('rex.show(rex.post("https://example.test/x", {"a": 1}).id)') == "2"
    assert fake.calls[0]["json"] == {"a": 1}


def test_request_returns_full_response(fake_http):
    fake_http(FakeResponse(payload={"a": 1}))
    source = """
rex.let r = rex.request("GET", "https://example.test/x")
rex.show(r.status, r.ok, r.json.a)
"""
    assert run(source) == ["200 true 1"]


def test_http_error_status_raises(fake_http):
    fake_http(FakeResponse(status_code=404, payload={"error": "gone"}))
    with pytest.raises(RexError) as excinfo:
        run('rex.get("https://example.test/x")')
    assert "HTTP 404" in excinfo.value.message


def test_transport_error_is_wrapped(fake_http):
    fake_http(RuntimeError("connection refused"))
    with pytest.raises(RexError) as excinfo:
        run('rex.get("https://example.test/x")')
    assert "connection refused" in excinfo.value.message


def test_unknown_http_option_is_rejected(fake_http):
    fake_http(FakeResponse(payload={}))
    with pytest.raises(RexError) as excinfo:
        run('rex.get("https://example.test/x", {"header": {}})')
    assert "unknown option" in excinfo.value.message


def test_text_response_falls_back_to_text(fake_http):
    fake_http(FakeResponse(payload=None, text="plain body", headers={"Content-Type": "text/plain"}))
    assert value('rex.show(rex.get("https://example.test/x"))') == "plain body"
