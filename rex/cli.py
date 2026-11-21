"""Command line interface for Rex.

Commands::

    rex run <file.rex> [args...]   run a program
    rex <file.rex> [args...]       shorthand for `rex run`
    rex repl                       interactive session
    rex check <file.rex>...        static checks, no execution
    rex ast <file.rex>             dump the parsed syntax tree as JSON
    rex init [dir]                 scaffold a new project
    rex version                    print the version
"""

from __future__ import annotations

import json
import os
import sys
from typing import List, Optional

from . import __version__
from .analyzer import analyze
from .errors import ExitSignal, RexError, RexImportError, RexSyntaxError
from .interpreter import DEFAULT_MAX_DEPTH, DEFAULT_MAX_STEPS, RexInterpreter
from .parser import parse

PROG = "rex"

EXIT_OK = 0
EXIT_RUNTIME = 1
EXIT_SYNTAX = 2
EXIT_USAGE = 3
EXIT_IMPORT = 4
EXIT_INTERRUPT = 130

USAGE = """\
Rex %s — a tiny, friendly scripting language for API work. Made in Mzansi.

usage:
  rex run <file.rex> [args...]   run a Rex program
  rex <file.rex> [args...]       shorthand for `rex run`
  rex repl                       interactive session
  rex check <file.rex>...        static checks without running
  rex ast <file.rex>             print the syntax tree as JSON
  rex init [dir]                 scaffold a new Rex project
  rex version                    print the version
  rex help                       this message

options:
  --max-steps <n>    statement budget before Rex aborts (default %d)
  --max-depth <n>    maximum nested function calls (default %d)
  -h, --help         show this help
  -v, --version      show the version

examples:
  rex run examples/hello.rex
  rex examples/api_fetch.rex
  rex check examples/hello.rex
  echo 'rex.show("hi")' > hi.rex && rex hi.rex
""" % (__version__, DEFAULT_MAX_STEPS, DEFAULT_MAX_DEPTH)

INIT_MAIN = '''\
# main.rex — a new Rex project
# Run it with:  rex run main.rex

rex.show("Sawubona Mhlaba")

rex.let url = "https://jsonplaceholder.typicode.com/posts/1"

rex.try
  rex.let post = rex.get(url)
  rex.show("title:", post.title)
rex.catch err
  rex.show("could not fetch:", err.message)
rex.end

rex.return
'''

INIT_README = """\
# %s

A Rex project. Rex is a tiny, friendly scripting language for API work.

```bash
pip install rex-lang
rex run main.rex
```

- Docs: https://alysiumcorporationstudios.github.io/Rex-Programming-Lang/
- Language reference: https://alysiumcorporationstudios.github.io/Rex-Programming-Lang/language/
"""


def main(argv: Optional[List[str]] = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args:
        print(USAGE)
        return EXIT_OK

    first = args[0]
    if first in ("-h", "--help", "help"):
        print(USAGE)
        return EXIT_OK
    if first in ("-v", "--version", "version"):
        print("Rex %s" % __version__)
        return EXIT_OK

    try:
        if first == "run":
            return command_run(args[1:])
        if first == "repl":
            from .repl import repl

            return repl()
        if first == "check":
            return command_check(args[1:])
        if first == "ast":
            return command_ast(args[1:])
        if first == "init":
            return command_init(args[1:])
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return EXIT_INTERRUPT
    except BrokenPipeError:  # pragma: no cover - depends on the shell
        return EXIT_OK

    if first.startswith("-"):
        print("unknown option %r\n" % first, file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return EXIT_USAGE

    if first.endswith(".rex") or os.path.isfile(first):
        return command_run(args)

    print("unknown command %r\n" % first, file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return EXIT_USAGE


def _split_flags(args: List[str]):
    """Pull global flags out of an argument list, keeping script args in order."""
    flags = {"max_steps": DEFAULT_MAX_STEPS, "max_depth": DEFAULT_MAX_DEPTH}
    rest: List[str] = []
    i = 0
    seen_separator = False
    while i < len(args):
        arg = args[i]
        if seen_separator:
            rest.append(arg)
            i += 1
            continue
        if arg == "--":
            seen_separator = True
            i += 1
            continue
        if arg in ("--max-steps", "--max-depth"):
            if i + 1 >= len(args):
                raise SystemExit(_usage_error("%s needs a value" % arg))
            value = args[i + 1]
            key = "max_steps" if arg == "--max-steps" else "max_depth"
            flags[key] = _positive_int(arg, value)
            i += 2
            continue
        if arg.startswith("--max-steps=") or arg.startswith("--max-depth="):
            name, _, value = arg.partition("=")
            key = "max_steps" if name == "--max-steps" else "max_depth"
            flags[key] = _positive_int(name, value)
            i += 1
            continue
        rest.append(arg)
        i += 1
    return flags, rest


def _positive_int(flag: str, value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise SystemExit(_usage_error("%s expects a whole number, got %r" % (flag, value))) from None
    if number <= 0:
        raise SystemExit(_usage_error("%s must be greater than 0" % flag))
    return number


def _usage_error(message: str) -> int:
    print("rex: %s" % message, file=sys.stderr)
    return EXIT_USAGE


def command_run(args: List[str]) -> int:
    try:
        flags, rest = _split_flags(args)
    except SystemExit as exc:
        return int(exc.code or EXIT_USAGE)

    if not rest:
        print("rex: no file given\n", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return EXIT_USAGE

    path = rest[0]
    script_args = rest[1:]
    if not os.path.isfile(path):
        print("Rex Error: file not found: %s" % path, file=sys.stderr)
        return EXIT_IMPORT

    interp = RexInterpreter(argv=script_args, max_steps=flags["max_steps"], max_depth=flags["max_depth"])
    try:
        interp.run_file(path)
    except RexSyntaxError as exc:
        print(exc.render(), file=sys.stderr)
        return EXIT_SYNTAX
    except RexImportError as exc:
        print(exc.render(), file=sys.stderr)
        return EXIT_IMPORT
    except RexError as exc:
        print(exc.render(), file=sys.stderr)
        return EXIT_RUNTIME
    except ExitSignal as signal:
        return signal.code
    except RecursionError:  # pragma: no cover - defensive
        print("Rex Error: maximum call depth exceeded", file=sys.stderr)
        return EXIT_RUNTIME
    return interp.exit_code


def command_check(args: List[str]) -> int:
    paths = [a for a in args if not a.startswith("-")]
    if not paths:
        print("rex check: no file given", file=sys.stderr)
        return EXIT_USAGE
    errors = 0
    for path in paths:
        if not os.path.isfile(path):
            print("%s: file not found" % path, file=sys.stderr)
            return EXIT_IMPORT
        try:
            with open(path, "r", encoding="utf-8") as handle:
                source = handle.read()
        except OSError as exc:
            print("%s: %s" % (path, exc), file=sys.stderr)
            return EXIT_IMPORT
        try:
            findings = analyze(source, path)
        except RexSyntaxError as exc:
            print(exc.render(), file=sys.stderr)
            errors += 1
            continue
        for finding in findings:
            print(finding.render(path))
            if finding.level == "error":
                errors += 1
        if not findings:
            print("%s: ok" % path)
    return EXIT_SYNTAX if errors else EXIT_OK


def command_ast(args: List[str]) -> int:
    paths = [a for a in args if not a.startswith("-")]
    if not paths:
        print("rex ast: no file given", file=sys.stderr)
        return EXIT_USAGE
    path = paths[0]
    try:
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        print("rex ast: %s" % exc, file=sys.stderr)
        return EXIT_IMPORT
    try:
        program = parse(source, path)
    except RexSyntaxError as exc:
        print(exc.render(), file=sys.stderr)
        return EXIT_SYNTAX
    print(json.dumps(program.to_dict(), indent=2))
    return EXIT_OK


def command_init(args: List[str]) -> int:
    target = args[0] if args else "."
    target = os.path.abspath(target)
    main_path = os.path.join(target, "main.rex")
    if os.path.exists(main_path):
        print("rex init: %s already exists" % main_path, file=sys.stderr)
        return EXIT_USAGE
    os.makedirs(target, exist_ok=True)
    with open(main_path, "w", encoding="utf-8") as handle:
        handle.write(INIT_MAIN)
    readme_path = os.path.join(target, "README.md")
    if not os.path.exists(readme_path):
        with open(readme_path, "w", encoding="utf-8") as handle:
            handle.write(INIT_README % os.path.basename(target))
    print("created %s" % main_path)
    try:
        shown = os.path.relpath(main_path)
    except ValueError:  # different drive on Windows
        shown = main_path
    print("next: rex run %s" % shown)
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
