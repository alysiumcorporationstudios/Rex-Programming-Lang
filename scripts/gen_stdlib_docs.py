#!/usr/bin/env python3
"""Generate `docs/stdlib.md` from the live standard library.

Run `python scripts/gen_stdlib_docs.py` to rewrite the reference, or
`python scripts/gen_stdlib_docs.py --check` to fail when it is out of date
(CI runs the check so the docs can never drift from the code).
"""

from __future__ import annotations

import os
import sys
from typing import Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from rex.builtins import make_stdlib  # noqa: E402
from rex.values import Builtin, Namespace  # noqa: E402

TARGET = os.path.join(ROOT, "docs", "stdlib.md")

HEADER = """\
# Standard library

Everything in Rex lives under the `rex` namespace, so a script never collides
with the language itself. This page is generated from the interpreter source by
`scripts/gen_stdlib_docs.py`, so it always matches the shipped behaviour.

```rex
rex.show("Sawubona")                                    # printing
rex.let post = rex.get("https://example.com/api/1")     # HTTP
rex.show(post.title)                                    # property access
rex.let slug = rex.replace(rex.lower(post.title), " ", "-")
rex.write("post.txt", rex.json.stringify(post, true))
```

## At a glance

| Group | Members |
|---|---|
"""


class _Stub:
    argv: List[str] = []
    version = "1.0.0"

    def write(self, text: str) -> None:  # pragma: no cover
        pass


def collect() -> List[tuple]:
    namespace = make_stdlib(_Stub())
    rows: List[tuple] = []

    def walk(path: str, node: Namespace) -> None:
        for key, value in node.items():
            child = "%s.%s" % (path, key)
            rows.append((child, value))
            if isinstance(value, Namespace):
                walk(child, value)

    walk("rex", namespace)
    return rows


def render() -> str:
    rows = collect()
    builtins = [(p, v) for p, v in rows if isinstance(v, Builtin)]
    values = [(p, v) for p, v in rows if not isinstance(v, Builtin)]
    groups: Dict[str, List[tuple]] = {}
    for path, builtin in builtins:
        groups.setdefault(path.rsplit(".", 1)[0], []).append((path, builtin))

    parts: List[str] = [HEADER]
    for group in sorted(groups):
        members = ", ".join("`%s`" % p.split(".")[-1] for p, _ in groups[group])
        parts.append("| `%s` | %s |\n" % (group, members))
    parts.append("\n%d functions and %d values.\n" % (len(builtins), len(values)))

    for group in sorted(groups):
        parts.append("\n## `%s`\n\n" % group)
        parts.append("| Function | Arguments | Description |\n|---|---|---|\n")
        for path, builtin in groups[group]:
            if builtin.max_args is None:
                arity = "%d or more" % builtin.min_args
            elif builtin.min_args == builtin.max_args:
                arity = str(builtin.min_args)
            else:
                arity = "%d to %d" % (builtin.min_args, builtin.max_args)
            parts.append("| `%s` | %s | %s |\n" % (path, arity, builtin.doc))

    if values:
        parts.append("\n## Values\n\n")
        for path, value in values:
            parts.append("- `%s` = `%s`\n" % (path, value))

    parts.append(
        """
## Behaviour worth knowing

- **Numbers** are integers or floats. Division always produces a float;
  `rex.math.round(x)` returns an integer when you ask for 0 digits.
- **Strings** support `${...}` interpolation in double quotes only. Single
  quotes are literal.
- **Truthiness**: `null`, `false`, `0`, `0.0`, `""`, `[]` and `{}` are false;
  everything else is true.
- **Equality** is structural and type aware, so `1 == true` is `false`.
- **HTTP** builtins return parsed JSON when the response is JSON, otherwise the
  response text. Use `rex.request()` when you need the status code or headers.
- **HTTP errors** are catchable Rex errors: a 404 raises, so wrap calls in
  `rex.try` / `rex.catch` when a missing resource is expected.
- **Files** are read and written as UTF-8. `rex.write` creates parent
  directories for you.
- **Copies vs mutation**: `rex.sort`, `rex.reverse`, `rex.unique` and
  `rex.clone` return copies. `rex.push` and `rex.pop` mutate in place, which is
  what you want inside a loop.
"""
    )
    return "".join(parts)


def main(argv: List[str]) -> int:
    content = render()
    if "--check" in argv:
        if not os.path.isfile(TARGET):
            print("docs/stdlib.md is missing; run python scripts/gen_stdlib_docs.py")
            return 1
        with open(TARGET, encoding="utf-8") as handle:
            current = handle.read()
        if current != content:
            print("docs/stdlib.md is out of date; run python scripts/gen_stdlib_docs.py")
            return 1
        print("docs/stdlib.md is up to date")
        return 0
    with open(TARGET, "w", encoding="utf-8") as handle:
        handle.write(content)
    print("wrote %s (%d bytes)" % (os.path.relpath(TARGET), len(content)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
