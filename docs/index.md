# Rex

**A tiny, friendly scripting language for API work.** Everything starts with `rex.`
Made in Mzansi. Built for developers who just want to fetch data and print it.

```rex
rex.show("Sawubona Mhlaba")

rex.let post = rex.get("https://jsonplaceholder.typicode.com/posts/1")
rex.show(post.title)

rex.for tag in ["api", "tiny", "mzansi"]
  rex.show("-", rex.upper(tag))
rex.end
```

Rex is a complete little language: real values, real control flow, real
functions with closures, real error handling, and an HTTP client that is part of
the language instead of an import you have to remember.

## Why Rex exists

Most scripting languages make you choose: either a friendly one-liner tool, or a
full language with a standard library you have to learn. Rex is the small one
that still behaves like a real language.

- **Namespaced by design.** Every builtin lives under `rex.`, so your own names
  never collide with the language and a reader can tell at a glance what is
  builtin and what is yours.
- **API-first.** `rex.get`, `rex.post`, `rex.json`, `rex.env` and file helpers
  ship in the box. No dependency hunting for a throwaway script.
- **One file, one command.** `rex run script.rex` and you are done.
- **Honest errors.** Every error carries a file, line, column, a caret under the
  offending token and, where possible, a hint.
- **Small enough to read.** The whole implementation is a lexer, a parser and a
  tree-walking interpreter you can read in an afternoon.

## What it looks like

```rex
# functions with defaults, closures and recursion
rex.func greet(who, greeting = "Sawubona")
  rex.return "${greeting}, ${who}!"
rex.end

rex.show(greet("Mhlaba"))
rex.show(greet("Andile", "Hello"))

# error handling that catches network failures
rex.try
  rex.let data = rex.get("https://example.com/api/items")
  rex.show("items:", rex.len(data))
rex.catch err
  rex.show("request failed:", err.message)
rex.end
```

## Install

```bash
pip install rex-lang
rex run hello.rex
```

Or from source:

```bash
git clone https://github.com/alysiumcorporationstudios/Rex-Programming-Lang
cd Rex-Programming-Lang
pip install -e .
rex run examples/hello.rex
```

Next: the [quick start](quickstart.md), the [language reference](language.md) and
the [standard library](stdlib.md).

## Status

Rex 1.0.0 is the first release with a stable language surface: the syntax,
builtins and CLI documented here are what the 1.x line guarantees. See the
[changelog](changelog.md) for what changed from the 0.1 prototype and the
[roadmap](roadmap.md) for what comes next.
