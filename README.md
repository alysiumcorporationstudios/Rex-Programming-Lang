
# Rex Lang 🇿🇦

Rex is a tiny, friendly scripting language for API work. Everything starts with `rex.`

Made in Mzansi. Built for developers who just want to fetch data and print it.

```rex
rex.show("Sawubona Mhlaba")
rex.let res = rex.get("https://jsonplaceholder.typicode.com/posts/1")
rex.show(res.title)
rex.return
```

## Install

```bash
pip install rex-lang
```

Or from source:
```bash
git clone https://github.com/alysiumcorp/rex-lang
cd rex-lang
pip install -e .
```

## Run

```bash
rex run example.rex
# or
rex example.rex
```

## Language — v0.1

| Command | Description |
|---|---|
| `rex.show(value)` | Print to stdout. Objects are pretty-printed as JSON |
| `rex.let name = value` | Assign a variable |
| `rex.get(url)` | Fetch JSON from a URL. Returns parsed object |
| `rex.post(url, data)` | POST JSON to a URL. Returns response |
| `rex.return` | Stop execution |
| `# comment` | Line comment |

Expressions: strings `"..."`, numbers, variables, property access `res.title`, `true` / `false` / `null`.

Files end in `.rex`.

## Examples

See `/examples`:
- `hello.rex` — hello world
- `api_fetch.rex` — fetch and print API data
- `variables.rex` — variables demo

Run them:
```bash
rex run examples/api_fetch.rex
```

## Why Rex?

- All builtins are namespaced: `rex.*` — no collisions, instantly recognizable
- API-first: `rex.get` is builtin, not an import
- Zero config: one file, one command
- Small and readable: the whole interpreter is ~120 lines of Python
- South African built 🇿🇦

## Roadmap

- v0.1 — `show`, `let`, `get`, `post`, `return` ✅
- v0.2 — `rex.if` / `rex.end`, comparisons, loops
- v0.3 — functions, modules, `rex.read` / `rex.write`
- v0.4 — VS Code extension, syntax highlighting for `.rex`

## Contributing

PRs welcome. Keep Rex small and friendly.

```bash
git clone https://github.com/alysiumcorp/rex-lang
cd rex-lang
pip install -e .
rex run examples/hello.rex
```

## License

MIT — see LICENSE

MIT License

Copyright (c) 2026 Andile Mtolo known as Toxic Dee Modder / Alysium Corp Studios

## The software (rex) was founded in South Africa and owned By Alysium Corp Studios ZA inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## Rex Lang v0.1 — Made in Mzansi 🇿🇦
