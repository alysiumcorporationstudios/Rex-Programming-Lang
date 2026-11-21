# Rex for VS Code

Syntax highlighting, snippets and comment support for the
[Rex scripting language](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang).

## Features

- Full syntax highlighting for the language: `rex.` control keywords, builtins,
  strings with `${}` interpolation, numbers, operators and comments.
- Function names in `rex.func name(...)` highlighted as definitions.
- `#` line comments (`Ctrl+/` / `Cmd+/`).
- Auto-closing brackets and quotes.
- Indentation rules so `rex.end` lines up with the block it closes.
- Snippets for `let`, `if`, `for`, `while`, `func`, `try`, `get`, `post`, `import`.

## Install

Not on the marketplace yet. Build it locally:

```bash
cd editors/vscode
npm install -g @vscode/vsce
vsce package
code --install-extension rex-lang-1.0.0.vsix
```

Or copy this folder into your extensions directory and restart VS Code.

## Language docs

https://alysiumcorporationstudios.github.io/Rex-Programming-Lang/

## License

MIT.
