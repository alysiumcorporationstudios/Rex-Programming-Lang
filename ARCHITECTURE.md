# Architecture

Rex is a classic tree-walking interpreter in about 2,500 lines of dependency-free
Python (plus `requests` for HTTP).

```
source text
    │
    ▼
lexer.py      characters → tokens          (line/col on every token)
    │
    ▼
parser.py     tokens → AST                 (recursive descent, precedence climbing)
    │
    ├──► analyzer.py   AST → findings      (`rex check`, no execution)
    │
    ▼
interpreter.py  AST → values               (scopes, closures, control flow)
    │
    ▼
builtins.py     the `rex` namespace        (60 native functions)
```

## Modules

| Module | Responsibility |
|---|---|
| `rex/lexer.py` | tokenises source, handles strings, interpolation flags, newline suppression, bracket depth |
| `rex/ast_nodes.py` | dataclass node definitions with `line`/`col`, plus `to_dict()` for `rex ast` |
| `rex/parser.py` | recursive descent parser; builds the AST; reports syntax errors with position |
| `rex/values.py` | runtime value helpers: `Builtin`, `RexFunction`, `Namespace`, truthiness, equality, formatting |
| `rex/interpreter.py` | `Scope`, `RexInterpreter`, statement execution, expression evaluation, imports, limits |
| `rex/builtins.py` | the standard library, assembled into the `rex` namespace |
| `rex/analyzer.py` | static checks used by `rex check` |
| `rex/cli.py` | argument parsing, subcommands, exit codes |
| `rex/repl.py` | interactive session, multi-line blocks, `:commands` |
| `rex/errors.py` | `RexError` hierarchy and the caret diagnostic renderer |

## Design decisions

**Everything is namespaced.** Builtins live under `rex.` so a script cannot
accidentally shadow `show` or `get`, and a reader can tell builtin from user code
at a glance. It also means adding a builtin never breaks existing programs.

**`rex.end` instead of indentation.** Blocks are explicit. Copy-pasting a snippet
cannot silently change its meaning because of leading whitespace, and the parser
can point at the missing terminator.

**One error type.** `RexError` carries a message, an optional hint and an
optional position. Builtins raise it, the interpreter raises it, `rex.try`
catches it, and the CLI renders it. There is no exception hierarchy for users to
learn.

**Errors are values you can inspect.** `rex.catch err` binds a dict with
`message`, `type`, `line`, `col` and `filename`, so handling a failure does not
require string parsing.

**Structural equality that respects types.** `1 == true` is `false`. Predictable
equality is worth more than convenience in a scripting language people use for
data.

**Limits, not freezes.** A statement budget and a call-depth cap turn infinite
loops and runaway recursion into ordinary catchable errors.

**Docs generated from code.** `scripts/gen_stdlib_docs.py` writes
`docs/stdlib.md` from the live namespace, and CI runs it with `--check`. The
reference cannot drift from the implementation.

## Adding a builtin

1. Write the function inside `make_stdlib()` in `rex/builtins.py`. Validate
   arguments with the `_need_str` / `_need_number` / `_need_list` helpers so
   errors read like the rest of the language.
2. Register it: `namespace["thing"] = Builtin("rex.thing", thing, min, max, "Doc.")`.
   Python keywords such as `assert` must be assigned by subscript.
3. Regenerate the reference: `python scripts/gen_stdlib_docs.py`.
4. Add a test in `tests/test_builtins.py`.

`rex check` learns about it automatically, including its argument count.

## Adding a statement

1. Add a node to `rex/ast_nodes.py`.
2. Parse it in `parser.py`: add the keyword to `CONTROL_KEYWORDS`, dispatch it in
   `parse_statement()`, and add a `parse_*` method that consumes its block.
3. Execute it in `interpreter.py` (`_exec`), and teach `analyzer.py` to walk it.
4. Document it in `docs/language.md` and `docs/spec.md`, and add tests to
   `tests/test_parser.py` and `tests/test_interpreter.py`.

## Testing

```bash
make test          # pytest
make lint          # ruff
make check         # rex check on every example
make examples      # run every example
```

The suite covers the lexer, parser, interpreter, every builtin, the CLI, the
analyzer and every example. HTTP is tested against a fake transport, so the tests
run offline.
