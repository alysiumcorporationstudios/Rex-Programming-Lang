# Roadmap

Rex 1.0 has a stable language. These are the directions next, roughly in order.

## 1.1 — ergonomics

- `rex.read_json` / `rex.write_json` convenience wrappers
- `rex.map`, `rex.filter`, `rex.reduce` (needs a lambda form first)
- `rex.retry(n, seconds)` for flaky endpoints
- `rex.csv.parse` / `rex.csv.stringify`
- `rex.date` helpers on top of `rex.time`

## 1.2 — tooling

- `rex fmt` — a canonical formatter built on the existing AST
- `rex test` — a tiny assertion runner for `.rex` test files
- `rex doc` — print a builtin's documentation from the CLI
- Publish the VS Code extension to the marketplace
- A tree-sitter grammar for editors that prefer it

## 1.3 — language

- lambdas: `rex.func(x) x * 2 rex.end` as an expression
- `rex.match` for pattern-style branching
- `rex.foreach` with index and value
- optional type annotations, checked by `rex check`
- `rex.export` for explicit module surfaces instead of include semantics

## 2.0 — candidates

- a bytecode compiler and VM (same semantics, faster loops)
- a package registry for `.rex` modules
- a REPL with completion and history
- WASM build for running Rex in the browser

## Not planned

- classes and inheritance. Dicts plus closures cover the same ground in a
  scripting language this size.
- implicit string/number coercion. Explicit is better, and the error message
  tells you what to write.
- a package manager before there is a registry to manage.

Have an idea? Open an issue with the `enhancement` label.
