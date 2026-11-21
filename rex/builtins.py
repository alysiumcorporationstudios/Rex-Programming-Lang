"""The Rex standard library: everything reachable under `rex.`.

All builtins are namespaced so a Rex script never collides with them::

    rex.show("hi")
    rex.let body = rex.get("https://api.example.com/items")
    rex.let name = rex.env("NAME", "world")

Sub-namespaces group related helpers: `rex.json`, `rex.math`, `rex.time`.
"""

from __future__ import annotations

import json
import math as _math
import os
import random as _random
import sys
import time as _time
import uuid as _uuid
from typing import Any, Dict, List, Optional

from .errors import ExitSignal, RexError
from .values import (
    Builtin,
    Namespace,
    describe_type,
    format_value,
    to_plain,
    truthy,
)

# --- argument validation -------------------------------------------------


def _type_error(name: str, position: int, expected: str, value: Any) -> RexError:
    return RexError(
        "%s(): argument %d must be a %s, got %s"
        % (name, position, expected, describe_type(value))
    )


def _need_str(name: str, position: int, value: Any) -> str:
    if not isinstance(value, str):
        raise _type_error(name, position, "string", value)
    return value


def _need_number(name: str, position: int, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _type_error(name, position, "number", value)
    return value


def _need_list(name: str, position: int, value: Any) -> list:
    if not isinstance(value, list):
        raise _type_error(name, position, "list", value)
    return value


def _need_dict(name: str, position: int, value: Any) -> dict:
    if not isinstance(value, dict):
        raise _type_error(name, position, "dict", value)
    return value


def _need_int(name: str, position: int, value: Any) -> int:
    number = _need_number(name, position, value)
    if float(number) != int(number):
        raise RexError("%s(): argument %d must be a whole number, got %s" % (name, position, format_value(number)))
    return int(number)


# --- HTTP ----------------------------------------------------------------


def _requests():
    try:
        import requests  # type: ignore
    except ImportError:  # pragma: no cover - depends on the environment
        raise RexError(
            "HTTP builtins need the 'requests' package",
            hint="install it with: pip install requests",
        ) from None
    return requests


def _http_options(name: str, options: Any) -> Dict[str, Any]:
    if options is None:
        return {}
    opts = _need_dict(name, 2, options)
    allowed = {"headers", "timeout", "params", "json", "data", "auth"}
    unknown = sorted(set(opts) - allowed)
    if unknown:
        raise RexError(
            "%s(): unknown option(s) %s" % (name, ", ".join(repr(u) for u in unknown)),
            hint="supported options are: " + ", ".join(sorted(allowed)),
        )
    return dict(opts)


def _http_call(method: str, url: str, options: Optional[dict], name: str) -> Dict[str, Any]:
    requests = _requests()
    opts = _http_options(name, options)
    timeout = opts.pop("timeout", 15)
    try:
        response = requests.request(method, url, timeout=timeout, **opts)
    except Exception as exc:  # requests raises a wide range of transport errors
        detail = str(exc).strip().splitlines()[0] if str(exc).strip() else type(exc).__name__
        if len(detail) > 160:
            detail = detail[:157] + "..."
        raise RexError("%s %s failed: %s" % (method, url, detail)) from None

    headers = dict(response.headers)
    text = response.text
    parsed: Any = None
    content_type = headers.get("Content-Type", "")
    if "json" in content_type.lower() or (text[:1] in ("{", "[") and text):
        try:
            parsed = response.json()
        except ValueError:
            parsed = None
    if not response.ok:
        snippet = text.strip().replace("\n", " ")[:200]
        raise RexError(
            "HTTP %d for %s %s%s" % (response.status_code, method, url, (": " + snippet) if snippet else "")
        )
    return {
        "status": response.status_code,
        "ok": response.ok,
        "headers": headers,
        "json": parsed,
        "text": text,
        "url": response.url,
    }


def _body_result(result: Dict[str, Any]) -> Any:
    """`rex.get` style calls return parsed JSON when there is any, else raw text."""
    return result["json"] if result["json"] is not None else result["text"]


# --- standard library ----------------------------------------------------


def make_stdlib(interp: Any) -> Namespace:
    """Build the `rex` namespace for one interpreter instance."""

    def show(*values: Any) -> None:
        if not values:
            interp.write("")
            return
        interp.write(" ".join(format_value(v) for v in values))

    def input_(prompt: Any = "") -> str:
        if prompt not in ("", None):
            interp.write(format_value(prompt))
        line = sys.stdin.readline()
        if line == "":
            return ""
        return line.rstrip("\n")

    def exit_(code: Any = 0) -> None:
        raise ExitSignal(_need_int("rex.exit", 1, code))

    def assert_(condition: Any, message: Any = "assertion failed") -> None:
        if not truthy(condition):
            raise RexError(format_value(message))

    def error(message: Any = "error") -> None:
        raise RexError(format_value(message))

    def env(name: Any, default: Any = None) -> Any:
        key = _need_str("rex.env", 1, name)
        return os.environ.get(key, default)

    def get(url: Any, options: Any = None) -> Any:
        return _body_result(_http_call("GET", _need_str("rex.get", 1, url), options, "rex.get"))

    def post(url: Any, data: Any = None, options: Any = None) -> Any:
        opts = _http_options("rex.post", options) if options is not None else {}
        if data is not None:
            opts.setdefault("json", to_plain(data))
        return _body_result(_http_call("POST", _need_str("rex.post", 1, url), opts, "rex.post"))

    def put(url: Any, data: Any = None, options: Any = None) -> Any:
        opts = _http_options("rex.put", options) if options is not None else {}
        if data is not None:
            opts.setdefault("json", to_plain(data))
        return _body_result(_http_call("PUT", _need_str("rex.put", 1, url), opts, "rex.put"))

    def patch(url: Any, data: Any = None, options: Any = None) -> Any:
        opts = _http_options("rex.patch", options) if options is not None else {}
        if data is not None:
            opts.setdefault("json", to_plain(data))
        return _body_result(_http_call("PATCH", _need_str("rex.patch", 1, url), opts, "rex.patch"))

    def delete(url: Any, options: Any = None) -> Any:
        return _body_result(_http_call("DELETE", _need_str("rex.delete", 1, url), options, "rex.delete"))

    def request(method: Any, url: Any, options: Any = None) -> Dict[str, Any]:
        verb = _need_str("rex.request", 1, method).upper()
        return _http_call(verb, _need_str("rex.request", 2, url), options, "rex.request")

    # files ---------------------------------------------------------------

    def read(path: Any) -> str:
        p = _need_str("rex.read", 1, path)
        try:
            with open(p, "r", encoding="utf-8") as handle:
                return handle.read()
        except FileNotFoundError:
            raise RexError("rex.read(): file not found: %s" % p) from None
        except OSError as exc:
            raise RexError("rex.read(): %s" % exc) from None

    def write(path: Any, content: Any) -> None:
        p = _need_str("rex.write", 1, path)
        text = content if isinstance(content, str) else format_value(content)
        try:
            parent = os.path.dirname(os.path.abspath(p))
            if parent and not os.path.isdir(parent):
                os.makedirs(parent, exist_ok=True)
            with open(p, "w", encoding="utf-8") as handle:
                handle.write(text)
        except OSError as exc:
            raise RexError("rex.write(): %s" % exc) from None

    def append(path: Any, content: Any) -> None:
        p = _need_str("rex.append", 1, path)
        text = content if isinstance(content, str) else format_value(content)
        try:
            with open(p, "a", encoding="utf-8") as handle:
                handle.write(text)
        except OSError as exc:
            raise RexError("rex.append(): %s" % exc) from None

    def exists(path: Any) -> bool:
        return os.path.exists(_need_str("rex.exists", 1, path))

    def list_files(directory: Any = ".") -> List[str]:
        d = _need_str("rex.list_files", 1, directory)
        try:
            return sorted(os.listdir(d))
        except OSError as exc:
            raise RexError("rex.list_files(): %s" % exc) from None

    # text ----------------------------------------------------------------

    def upper(value: Any) -> str:
        return _need_str("rex.upper", 1, value).upper()

    def lower(value: Any) -> str:
        return _need_str("rex.lower", 1, value).lower()

    def trim(value: Any) -> str:
        return _need_str("rex.trim", 1, value).strip()

    def split(value: Any, separator: Any = None) -> List[str]:
        text = _need_str("rex.split", 1, value)
        if separator is None:
            return text.split()
        return text.split(_need_str("rex.split", 2, separator))

    def join(values: Any, separator: Any = "") -> str:
        items = _need_list("rex.join", 1, values)
        sep = _need_str("rex.join", 2, separator) if separator is not None else ""
        return sep.join(format_value(v) for v in items)

    def replace(value: Any, old: Any, new: Any) -> str:
        return _need_str("rex.replace", 1, value).replace(
            _need_str("rex.replace", 2, old), _need_str("rex.replace", 3, new)
        )

    def contains(haystack: Any, needle: Any) -> bool:
        if isinstance(haystack, str):
            return _need_str("rex.contains", 2, needle) in haystack
        if isinstance(haystack, list):
            from .values import equals

            return any(equals(item, needle) for item in haystack)
        if isinstance(haystack, dict):
            return str(needle) in haystack
        raise RexError("rex.contains(): argument 1 must be a string, list or dict, got %s" % describe_type(haystack))

    def starts_with(value: Any, prefix: Any) -> bool:
        return _need_str("rex.starts_with", 1, value).startswith(_need_str("rex.starts_with", 2, prefix))

    def ends_with(value: Any, suffix: Any) -> bool:
        return _need_str("rex.ends_with", 1, value).endswith(_need_str("rex.ends_with", 2, suffix))

    def repeat(value: Any, times: Any) -> str:
        return _need_str("rex.repeat", 1, value) * max(0, _need_int("rex.repeat", 2, times))

    # collections ---------------------------------------------------------

    def length(value: Any) -> int:
        if isinstance(value, (str, list, dict)):
            return len(value)
        raise RexError("rex.len(): expected a string, list or dict, got %s" % describe_type(value))

    def push(values: Any, *items: Any) -> list:
        target = _need_list("rex.push", 1, values)
        target.extend(items)
        return target

    def pop(values: Any, index: Any = None) -> Any:
        target = _need_list("rex.pop", 1, values)
        if not target:
            return None
        if index is None:
            return target.pop()
        idx = _need_int("rex.pop", 2, index)
        if not -len(target) <= idx < len(target):
            raise RexError("rex.pop(): index %d is out of range for a list of %d item(s)" % (idx, len(target)))
        return target.pop(idx)

    def keys(value: Any) -> List[str]:
        return list(_need_dict("rex.keys", 1, value).keys())

    def values_(value: Any) -> List[Any]:
        return list(_need_dict("rex.values", 1, value).values())

    def has(container: Any, key: Any) -> bool:
        if isinstance(container, dict):
            return str(key) in container
        if isinstance(container, list):
            return 0 <= _need_int("rex.has", 2, key) < len(container)
        raise RexError("rex.has(): argument 1 must be a dict or list, got %s" % describe_type(container))

    def range_(start: Any, stop: Any = None, step: Any = 1) -> List[int]:
        if stop is None:
            start, stop = 0, start
        a = _need_int("rex.range", 1, start)
        b = _need_int("rex.range", 2, stop)
        s = _need_int("rex.range", 3, step)
        if s == 0:
            raise RexError("rex.range(): step cannot be 0")
        return list(range(a, b, s))

    def sort(values: Any, descending: Any = False) -> list:
        target = list(_need_list("rex.sort", 1, values))
        try:
            target.sort(key=_sort_key, reverse=truthy(descending))
        except TypeError:
            raise RexError("rex.sort(): list contains values that cannot be compared") from None
        return target

    def reverse(values: Any) -> list:
        if isinstance(values, str):
            return values[::-1]
        return list(reversed(_need_list("rex.reverse", 1, values)))

    def sum_(values: Any) -> float:
        total = 0
        for item in _need_list("rex.sum", 1, values):
            total += _need_number("rex.sum", 1, item)
        return total

    def first(values: Any) -> Any:
        target = _need_list("rex.first", 1, values)
        return target[0] if target else None

    def last(values: Any) -> Any:
        target = _need_list("rex.last", 1, values)
        return target[-1] if target else None

    def unique(values: Any) -> list:
        from .values import equals

        result: list = []
        for item in _need_list("rex.unique", 1, values):
            if not any(equals(item, seen) for seen in result):
                result.append(item)
        return result

    # conversion ----------------------------------------------------------

    def type_of(value: Any) -> str:
        return describe_type(value)

    def to_string(value: Any = "") -> str:
        return format_value(value)

    def to_number(value: Any = 0) -> float:
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            text = value.strip()
            try:
                return int(text)
            except ValueError:
                try:
                    return float(text)
                except ValueError:
                    raise RexError("rex.num(): cannot convert %r to a number" % value) from None
        raise RexError("rex.num(): cannot convert %s to a number" % describe_type(value))

    def to_bool(value: Any = False) -> bool:
        return truthy(value)

    def clone(value: Any) -> Any:
        if isinstance(value, list):
            return [clone(v) for v in value]
        if isinstance(value, dict):
            return {k: clone(v) for k, v in value.items()}
        return value

    # json ----------------------------------------------------------------

    def json_parse(text: Any) -> Any:
        raw = _need_str("rex.json.parse", 1, text)
        try:
            return json.loads(raw)
        except ValueError as exc:
            raise RexError("rex.json.parse(): invalid JSON (%s)" % exc) from None

    def json_stringify(value: Any = None, pretty: Any = False) -> str:
        try:
            return json.dumps(to_plain(value), indent=2 if truthy(pretty) else None, ensure_ascii=False)
        except (TypeError, ValueError) as exc:  # pragma: no cover - to_plain normalises everything
            raise RexError("rex.json.stringify(): %s" % exc) from None

    # time ----------------------------------------------------------------

    def time_now() -> str:
        return _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime())

    def time_timestamp() -> float:
        return _time.time()

    def time_sleep(seconds: Any) -> None:
        _time.sleep(max(0.0, float(_need_number("rex.time.sleep", 1, seconds))))

    # math ----------------------------------------------------------------

    def math_sqrt(value: Any) -> float:
        number = _need_number("rex.math.sqrt", 1, value)
        if number < 0:
            raise RexError("rex.math.sqrt(): cannot take the square root of a negative number")
        return _math.sqrt(number)

    def math_floor(value: Any) -> int:
        return _math.floor(_need_number("rex.math.floor", 1, value))

    def math_ceil(value: Any) -> int:
        return _math.ceil(_need_number("rex.math.ceil", 1, value))

    def math_round(value: Any, digits: Any = 0) -> float:
        number = _need_number("rex.math.round", 1, value)
        places = _need_int("rex.math.round", 2, digits)
        rounded = round(number, places)
        return int(rounded) if places <= 0 else rounded

    def math_abs(value: Any) -> float:
        return abs(_need_number("rex.math.abs", 1, value))

    def math_pow(base: Any, exponent: Any) -> float:
        return _need_number("rex.math.pow", 1, base) ** _need_number("rex.math.pow", 2, exponent)

    def math_random() -> float:
        return _random.random()

    def math_min(*values: Any) -> float:
        numbers = _numbers_from("rex.math.min", values)
        return min(numbers)

    def math_max(*values: Any) -> float:
        numbers = _numbers_from("rex.math.max", values)
        return max(numbers)

    # misc ----------------------------------------------------------------

    def uuid4() -> str:
        return str(_uuid.uuid4())

    namespace = Namespace(
        "rex",
        show=Builtin("rex.show", show, 0, None, "Print values to stdout."),
        input=Builtin("rex.input", input_, 0, 1, "Read one line from stdin."),
        exit=Builtin("rex.exit", exit_, 0, 1, "Stop the program with an exit code."),
        error=Builtin("rex.error", error, 0, 1, "Raise a runtime error."),
        env=Builtin("rex.env", env, 1, 2, "Read an environment variable."),
        get=Builtin("rex.get", get, 1, 2, "HTTP GET, returns parsed JSON or text."),
        post=Builtin("rex.post", post, 1, 3, "HTTP POST with a JSON body."),
        put=Builtin("rex.put", put, 1, 3, "HTTP PUT with a JSON body."),
        patch=Builtin("rex.patch", patch, 1, 3, "HTTP PATCH with a JSON body."),
        delete=Builtin("rex.delete", delete, 1, 2, "HTTP DELETE."),
        request=Builtin("rex.request", request, 2, 3, "Full HTTP response as a dict."),
        read=Builtin("rex.read", read, 1, 1, "Read a UTF-8 file."),
        write=Builtin("rex.write", write, 2, 2, "Write a UTF-8 file."),
        append=Builtin("rex.append", append, 2, 2, "Append to a UTF-8 file."),
        exists=Builtin("rex.exists", exists, 1, 1, "True when a path exists."),
        list_files=Builtin("rex.list_files", list_files, 0, 1, "Names inside a directory."),
        upper=Builtin("rex.upper", upper, 1, 1, "Uppercase a string."),
        lower=Builtin("rex.lower", lower, 1, 1, "Lowercase a string."),
        trim=Builtin("rex.trim", trim, 1, 1, "Strip surrounding whitespace."),
        split=Builtin("rex.split", split, 1, 2, "Split a string into a list."),
        join=Builtin("rex.join", join, 1, 2, "Join a list into a string."),
        replace=Builtin("rex.replace", replace, 3, 3, "Replace every occurrence of a substring."),
        contains=Builtin("rex.contains", contains, 2, 2, "Membership test for strings, lists and dicts."),
        starts_with=Builtin("rex.starts_with", starts_with, 2, 2, "Prefix test."),
        ends_with=Builtin("rex.ends_with", ends_with, 2, 2, "Suffix test."),
        repeat=Builtin("rex.repeat", repeat, 2, 2, "Repeat a string n times."),
        len=Builtin("rex.len", length, 1, 1, "Length of a string, list or dict."),
        push=Builtin("rex.push", push, 2, None, "Append items to a list."),
        pop=Builtin("rex.pop", pop, 1, 2, "Remove and return a list item."),
        keys=Builtin("rex.keys", keys, 1, 1, "Keys of a dict."),
        values=Builtin("rex.values", values_, 1, 1, "Values of a dict."),
        has=Builtin("rex.has", has, 2, 2, "True when a key or index exists."),
        range=Builtin("rex.range", range_, 1, 3, "List of numbers."),
        sort=Builtin("rex.sort", sort, 1, 2, "Sorted copy of a list."),
        reverse=Builtin("rex.reverse", reverse, 1, 1, "Reversed copy of a list or string."),
        sum=Builtin("rex.sum", sum_, 1, 1, "Sum of a list of numbers."),
        first=Builtin("rex.first", first, 1, 1, "First item of a list."),
        last=Builtin("rex.last", last, 1, 1, "Last item of a list."),
        unique=Builtin("rex.unique", unique, 1, 1, "De-duplicated copy of a list."),
        type=Builtin("rex.type", type_of, 1, 1, "Rex type name of a value."),
        str=Builtin("rex.str", to_string, 0, 1, "Convert a value to a string."),
        num=Builtin("rex.num", to_number, 0, 1, "Convert a value to a number."),
        bool=Builtin("rex.bool", to_bool, 0, 1, "Convert a value to a boolean."),
        clone=Builtin("rex.clone", clone, 1, 1, "Deep copy of a list or dict."),
        uuid=Builtin("rex.uuid", uuid4, 0, 0, "Random UUID v4 string."),
        json=Namespace(
            "rex.json",
            parse=Builtin("rex.json.parse", json_parse, 1, 1, "Parse a JSON string."),
            stringify=Builtin("rex.json.stringify", json_stringify, 0, 2, "Serialise a value to JSON."),
        ),
        time=Namespace(
            "rex.time",
            now=Builtin("rex.time.now", time_now, 0, 0, "Current UTC time as ISO 8601."),
            timestamp=Builtin("rex.time.timestamp", time_timestamp, 0, 0, "Seconds since the epoch."),
            sleep=Builtin("rex.time.sleep", time_sleep, 1, 1, "Pause for n seconds."),
        ),
        math=Namespace(
            "rex.math",
            sqrt=Builtin("rex.math.sqrt", math_sqrt, 1, 1, "Square root."),
            floor=Builtin("rex.math.floor", math_floor, 1, 1, "Round down."),
            ceil=Builtin("rex.math.ceil", math_ceil, 1, 1, "Round up."),
            round=Builtin("rex.math.round", math_round, 1, 2, "Round to n digits."),
            abs=Builtin("rex.math.abs", math_abs, 1, 1, "Absolute value."),
            pow=Builtin("rex.math.pow", math_pow, 2, 2, "Raise to a power."),
            random=Builtin("rex.math.random", math_random, 0, 0, "Random number in [0, 1)."),
            min=Builtin("rex.math.min", math_min, 1, None, "Smallest number."),
            max=Builtin("rex.math.max", math_max, 1, None, "Largest number."),
            pi=_math.pi,
            e=_math.e,
        ),
    )
    namespace["assert"] = Builtin("rex.assert", assert_, 1, 2, "Fail unless the condition is truthy.")
    namespace["args"] = interp.argv
    namespace["version"] = interp.version
    return namespace


def _sort_key(value: Any) -> Any:
    if value is None:
        return (0, 0)
    if isinstance(value, bool):
        return (1, int(value))
    if isinstance(value, (int, float)):
        return (2, value)
    if isinstance(value, str):
        return (3, value)
    return (4, format_value(value))


def _numbers_from(name: str, values: Any) -> List[float]:
    if len(values) == 1 and isinstance(values[0], list):
        return [_need_number(name, 1, v) for v in values[0]]
    return [_need_number(name, i + 1, v) for i, v in enumerate(values)]


def builtin_index(namespace: Namespace) -> Dict[str, Builtin]:
    """Flat map of every builtin, used by `rex check` and the docs generator."""
    found: Dict[str, Builtin] = {}

    def walk(prefix: str, node: Any) -> None:
        for key, value in node.items():
            path = "%s.%s" % (prefix, key)
            if isinstance(value, Namespace):
                walk(path, value)
            elif isinstance(value, Builtin):
                found[path] = value

    walk("rex", namespace)
    return found
