# Contributing

Rex stays small on purpose, so the bar is simple: make it clearer, keep it
friendly, add tests.

## Set up

```bash
git clone https://github.com/alysiumcorporationstudios/Rex-Programming-Lang
cd Rex-Programming-Lang
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,docs]"
pre-commit install
```

## Before you open a pull request

```bash
make test        # pytest
make lint        # ruff
make check       # rex check on every example
python scripts/gen_stdlib_docs.py --check
```

All four must pass. CI runs the same commands on Python 3.8 through 3.13.

## What a good change looks like

- **Tests first.** A bug fix needs a test that fails before it. A builtin needs
  tests for the happy path and for the error paths.
- **Errors are part of the API.** Every new error message should say what went
  wrong and, where possible, how to fix it.
- **Documentation is part of the change.** New syntax goes in
  `docs/language.md` and `docs/spec.md`; new builtins get a docstring in
  `rex/builtins.py` and a regenerated `docs/stdlib.md`.
- **No new runtime dependencies.** The interpreter uses the standard library
  plus `requests`.
- **Keep it readable.** If a change makes the interpreter harder to follow, it
  needs a very good reason.

## Adding a builtin or a statement

See [ARCHITECTURE.md](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/ARCHITECTURE.md) for the step-by-step recipe.

## Commit messages

```
feat: add rex.csv.parse
fix: report imported-file line numbers in errors
docs: clarify block scoping
test: cover negative string indexes
chore: bump ruff
```

## Reporting bugs

Include the Rex version (`rex version`), the smallest program that reproduces
it, what you expected and what happened. If it is a diagnostic problem, paste the
full rendered error.

## Code of conduct

Be decent. See [CODE_OF_CONDUCT.md](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/CODE_OF_CONDUCT.md).
