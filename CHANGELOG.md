# Changelog

All notable changes to Rex are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[semantic versioning](https://semver.org/).

## [1.0.0] — 2026-11-21

The first release with a stable language. Rex is no longer a line-by-line regex
prototype: it is a lexer, a parser and a tree-walking interpreter.

### Added

- **Language**
  - `rex.if` / `rex.elif` / `rex.else` / `rex.end`
  - `rex.while` and `rex.for ... in` with `rex.break`, `rex.continue`, `rex.pass`
  - `rex.func` with default parameters, recursion and lexical closures
  - `rex.try` / `rex.catch` / `rex.throw`
  - `rex.import "file.rex"`
  - lists, dicts, indexing, member access, index and member assignment
  - full operator set with precedence: `+ - * / %`, comparisons, `and or not`
    (and `&& || !`), unary minus
  - `${...}` string interpolation in double-quoted strings
  - negative list and string indexes
  - block scoping with assignment that walks outward
- **Standard library** — 60 builtins under `rex.`: HTTP (`get`, `post`, `put`,
  `patch`, `delete`, `request`), files (`read`, `write`, `append`, `exists`,
  `list_files`), JSON (`rex.json.parse`, `rex.json.stringify`), text, collections,
  `rex.math`, `rex.time`, `rex.env`, `rex.assert`, `rex.exit`, type conversion.
- **CLI** — `run`, `repl`, `check`, `ast`, `init`, `version`, plus
  `--max-steps` and `--max-depth`.
- **`rex check`** — static analysis: unknown builtins, builtin argument counts and
  undefined variables, without running the program.
- **Diagnostics** — every error reports file, line, column, a caret under the
  offending token and, where possible, a hint.
- **Docs** — a documentation site (MkDocs Material), a language reference, a
  generated standard-library reference, a CLI guide, a formal spec and an
  architecture page.
- **Examples** — 14 runnable programs.
- **Tests** — 203 tests covering the lexer, parser, interpreter, stdlib, CLI,
  analyzer and examples.
- **Tooling** — `pyproject.toml` packaging, `make` targets, ruff, pre-commit,
  editorconfig, GitHub Actions CI, a VS Code extension with syntax highlighting.

### Changed

- `rex.get` and friends now raise a catchable Rex error on a non-2xx response
  instead of failing silently, and accept an options dict
  (`headers`, `timeout`, `params`, `json`, `data`, `auth`).
- Reading a missing dict key is an error that lists available keys instead of
  returning `null`.
- `rex.post(url, data)` keeps its 0.1 signature but now accepts an options dict
  as a third argument.
- The MIT license file was rewritten to the canonical text so GitHub detects it.
- Package metadata: `Development Status :: 5 - Production/Stable`, Python
  3.8–3.13 classifiers, project URLs, keywords.

### Fixed

- `rex/cli.py` contained a real newline inside a string literal, so the package
  could not be imported at all (`SyntaxError`). The CLI is rewritten.
- Strings, comments and brackets inside string literals no longer confuse the
  parser.
- `rex.post` with a body containing a comma was split at the wrong comma.
- Errors inside imported files now report the imported file's name and line.

### Compatibility

Every 0.1 program still runs. `rex.return` at the top level still ends the script;
inside a function it returns a value.

## [0.1.0] — 2026-06-14

- Initial prototype: `rex.show`, `rex.let`, `rex.get`, `rex.post`, `rex.return`,
  `#` comments, one statement per line, ~120 lines of Python.
