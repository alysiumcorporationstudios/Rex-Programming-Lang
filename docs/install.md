# Install

## Requirements

- Python 3.8 or newer
- `requests` (installed automatically with Rex)

## From PyPI

```bash
pip install rex-lang
rex version
```

## From source

```bash
git clone https://github.com/alysiumcorporationstudios/Rex-Programming-Lang
cd Rex-Programming-Lang
pip install -e .
```

`pip install -e .` puts the `rex` command on your PATH and makes the package
importable, which is what you want while working on the language itself.

## Without installing

You can run Rex straight from a checkout:

```bash
python -m rex run examples/hello.rex
```

## Use it as a library

```python
from rex import RexInterpreter, RexError

interp = RexInterpreter()
try:
    output = interp.run_source('rex.show("Sawubona")')
except RexError as error:
    print(error.render())
else:
    print(output)  # ['Sawubona']
```

`run_source()` and `run_file()` return every line `rex.show` printed, so you can
assert on Rex output from Python tests.

## Editor support

A VS Code extension with syntax highlighting and snippets lives in
[`editors/vscode`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/tree/main/editors/vscode).
It is not on the marketplace yet; install it from source:

```bash
cd editors/vscode
npm install -g @vscode/vsce
vsce package
code --install-extension rex-lang-1.0.0.vsix
```

## Upgrading from 0.1

The 0.1 prototype only understood `rex.show`, `rex.let`, `rex.get`, `rex.post`
and `rex.return`, one statement per line. Every 0.1 program still runs on 1.0.
The one behavioural difference: `rex.return` at the top level now stops the
script (it used to be the only way to end a file, and still works that way).
