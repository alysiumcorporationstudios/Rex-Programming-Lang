# Command line

```
rex run <file.rex> [args...]   run a Rex program
rex <file.rex> [args...]       shorthand for `rex run`
rex repl                       interactive session
rex check <file.rex>...        static checks without running
rex ast <file.rex>             print the syntax tree as JSON
rex init [dir]                 scaffold a new Rex project
rex version                    print the version
rex help                       full usage
```

## `rex run`

```bash
rex run examples/api_fetch.rex
```

Everything after the file path is passed to the script as `rex.args`:

```bash
rex run examples/env_args.rex one two
```

```rex
rex.show(rex.args)   # ["one", "two"]
```

Use `--` to pass arguments that look like flags:

```bash
rex run script.rex -- --verbose
```

| Flag | Default | Meaning |
|---|---|---|
| `--max-steps <n>` | 5000000 | statements to execute before aborting |
| `--max-depth <n>` | 200 | nested function calls allowed |

## `rex repl`

```bash
$ rex repl
Rex 1.0.0 — type :help for commands, Ctrl-D to leave
rex> rex.let name = "Rex"
rex> "hello ${name}"
hello Rex
rex> rex.for i in rex.range(0, 3)
...> rex.show(i)
...> rex.end
0
1
2
```

Bare expressions print their value. Blocks can be typed over several lines: the
prompt switches to `...>` until the block closes. `:vars` lists what you have
defined, `:clear` forgets it, `:quit` leaves.

## `rex check`

`rex check` parses a file and runs static checks without executing it. It catches
the mistakes that cost the most time:

```bash
$ rex check examples/hello.rex
examples/hello.rex: ok

$ rex check demo.rex
demo.rex:2:8: error: unknown builtin 'rex.sho'
demo.rex:5:12: warning: undefined variable 'titel'
demo.rex:9:8: error: rex.len() takes 1 argument(s) but 0 given
```

- **error**: unknown `rex.*` member, wrong builtin argument count, syntax error
- **warning**: reading a variable that was never declared

It exits non-zero when there is an error, so it drops straight into CI:

```bash
for f in examples/*.rex; do rex check "$f" || exit 1; done
```

After a `rex.import`, name checks for that file relax, because imported names are
not known statically.

## `rex ast`

Dumps the parsed syntax tree as JSON. Useful when you are curious how something
parses, or when you are writing a tool on top of Rex.

```bash
rex ast examples/hello.rex | head -20
```

## `rex init`

```bash
rex init my-project
cd my-project
rex run main.rex
```

Creates `main.rex` with a working example and a `README.md`. It refuses to
overwrite an existing `main.rex`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 1 | runtime error (thrown, HTTP failure, type error, limit hit) |
| 2 | syntax error, or `rex check` found an error |
| 3 | usage error (bad flag, unknown command, no file) |
| 4 | file not found or unreadable |
| 130 | interrupted with Ctrl-C |

Scripts can set the code themselves with `rex.exit(n)`.

## Using Rex from Python

```python
from rex import RexInterpreter

interp = RexInterpreter(argv=["one"])
print(interp.run_source('rex.show("hi")'))   # ['hi']
print(interp.exit_code)
```
