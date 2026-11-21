# Language reference

This is the complete Rex 1.0 language. If it is not on this page, it is not in
the language.

## The shape of a program

A Rex program is a list of statements, one per line. Every builtin and every
control-flow keyword starts with `rex.`, so the language is always visible in
your code:

```rex
rex.show("one statement per line")
rex.let answer = 42
```

- `#` starts a comment that runs to the end of the line.
- Blank lines are ignored.
- Statements end at the end of a line. Expressions may continue across lines
  inside brackets, after a comma or a binary operator, or after a trailing `\`.
- Files use the `.rex` extension.

```rex
rex.let totals = [
  12.50,
  4.00,
  9.99,
]

rex.let sum = 12.50 +
             4.00
```

## Values

| Type | Example | Notes |
|---|---|---|
| number | `42`, `-3.5`, `1e3` | integers and floats, no separate types |
| string | `"hello"`, `'literal'` | double quotes interpolate, single quotes do not |
| boolean | `true`, `false` | |
| null | `null` | the absence of a value |
| list | `[1, "two", true]` | ordered, indexable, mutable |
| dict | `{"name": "Rex"}` | string keys, insertion ordered |
| function | `rex.func` | a value you can pass around and return |
| builtin | `rex.show` | native functions on the `rex` namespace |

`rex.type(value)` returns the type name as a string.

## Variables

```rex
rex.let name = "Andile"     # declare
name = "Toxic Dee Modder"   # reassign
rex.show(name)
```

`rex.let` declares a name in the current scope. Plain assignment (`=`) finds the
nearest existing declaration and updates it, which is how you accumulate inside a
loop:

```rex
rex.let total = 0
rex.for n in [1, 2, 3]
  total = total + n
rex.end
rex.show(total)   # 6
```

Assigning to a name that was never declared is an error, with a hint to use
`rex.let`:

```
Rex Error: cannot assign to undefined variable 'total'
  hint: declare it first with rex.let total = ...
```

You can also assign into a structure:

```rex
rex.let user = {"name": "Andile"}
user.name = "Toxic Dee Modder"
user["country"] = "South Africa"

rex.let items = [1, 2, 3]
items[0] = 99
```

## Blocks and control flow

Every block is opened by a `rex.` keyword and closed by `rex.end`. Indentation is
for humans; it is not syntax.

### `rex.if` / `rex.elif` / `rex.else`

```rex
rex.if score >= 90
  rex.show("A")
rex.elif score >= 75
  rex.show("B")
rex.elif score >= 60
  rex.show("C")
rex.else
  rex.show("keep going")
rex.end
```

### `rex.while`

```rex
rex.let countdown = 3
rex.while countdown > 0
  rex.show(countdown)
  countdown = countdown - 1
rex.end
```

### `rex.for`

```rex
rex.for city in ["Johannesburg", "Durban"]
  rex.show(city)
rex.end
```

`rex.for` walks a list (items), a string (characters) or a dict (keys). Numbers
are not iterable on purpose, and the error tells you what to write instead:

```
Rex Error: cannot loop over a number
  hint: use rex.range(0, 5)
```

### `rex.break`, `rex.continue`, `rex.pass`

```rex
rex.for n in rex.range(0, 10)
  rex.if n == 2
    rex.continue
  rex.end
  rex.if n == 4
    rex.break
  rex.end
  rex.show(n)
rex.end
```

`rex.pass` is a no-op, useful as the placeholder body of a block you have not
written yet.

### Scopes

`rex.if`, `rex.while`, `rex.for` and `rex.try` bodies run in a child scope, so a
`rex.let` inside a block belongs to that block:

```rex
rex.if true
  rex.let inner = 1
rex.end
rex.show(inner)   # Rex Error: undefined variable 'inner'
```

Assignment is different: it searches outward and updates the existing variable.
That is why `total = total + n` inside a loop works, and why you should declare
your accumulators before the loop.

## Functions

```rex
rex.func greet(who, greeting = "Sawubona")
  rex.return "${greeting}, ${who}!"
rex.end

rex.show(greet("Mhlaba"))            # Sawubona, Mhlaba!
rex.show(greet("Andile", "Hello"))   # Hello, Andile!
```

- Parameters may have defaults. Defaults are evaluated in the scope where the
  function was defined, not at the call site.
- A function without `rex.return` returns `null`.
- Calling with too many or too few arguments is an error, caught at runtime and
  by `rex check`.
- Functions are values. You can store them, pass them and return them.

### Closures

A function remembers the scope it was created in:

```rex
rex.func make_counter()
  rex.let total = 0
  rex.func bump(step = 1)
    total = total + step
    rex.return total
  rex.end
  rex.return bump
rex.end

rex.let counter = make_counter()
rex.show(counter(), counter(5), counter(2))   # 1 6 8
```

### Recursion

```rex
rex.func factorial(n)
  rex.if n <= 1
    rex.return 1
  rex.end
  rex.return n * factorial(n - 1)
rex.end
```

Nesting is capped at 200 calls by default (`--max-depth`), so runaway recursion
fails with a clear message instead of a Python traceback.

### `rex.return` at the top level

Inside a function, `rex.return` leaves the function. At the top level it stops
the script, which is how 0.1 programs ended:

```rex
rex.show("this runs")
rex.return
rex.show("this does not")
```

## Operators

From loosest to tightest binding:

| Precedence | Operators | Notes |
|---|---|---|
| 1 | `or`, `\|\|` | returns the left value when truthy, else the right |
| 2 | `and`, `&&` | returns the left value when falsy, else the right |
| 3 | `not`, `!` | always returns a boolean |
| 4 | `==`, `!=`, `<`, `<=`, `>`, `>=` | chained left to right |
| 5 | `+`, `-` | numbers, strings and lists for `+` |
| 6 | `*`, `/`, `%` | numbers; `*` also repeats strings and lists |
| 7 | unary `-`, unary `+` | |
| 8 | `()`, `[]`, `.` | call, index, member |

`and`, `or` and `not` short-circuit and accept the symbolic forms `&&`, `||`,
`!`.

### Arithmetic

```rex
rex.show(1 + 2)        # 3
rex.show(10 / 4)       # 2.5   division always produces a float
rex.show(10 % 3)       # 1
rex.show(2 + 3 * 4)    # 14
rex.show("ab" * 3)     # ababab
rex.show([1] + [2])    # [1, 2]
```

Adding a string and a number is an error rather than a surprise, and the hint
points at interpolation:

```
Rex Error: cannot add string and number
  hint: join text with rex.str() or "text ${value}" interpolation
```

Division or modulo by zero is an error.

### Comparison and equality

`<`, `<=`, `>`, `>=` work between two numbers or two strings. Anything else is
an error.

`==` and `!=` are structural and type aware: lists and dicts compare by content,
and booleans never equal numbers.

```rex
rex.show([1, 2] == [1, 2])        # true
rex.show({"a": 1} == {"a": 1})    # true
rex.show(1 == true)               # false
```

### Truthiness

`null`, `false`, `0`, `0.0`, `""`, `[]` and `{}` are false. Everything else is
true.

```rex
rex.if rex.len(items)
  rex.show("we have items")
rex.end
```

## Strings

Double-quoted strings support `${...}` interpolation with any expression inside:

```rex
rex.let name = "Rex"
rex.show("hello ${name}, 1 + 1 = ${1 + 1}")
rex.show("${rex.upper(name)} in a hole")
```

Single-quoted strings are literal, which is handy for JSON:

```rex
rex.let payload = '{"a": 1}'
rex.let data = rex.json.parse(payload)
```

Escape sequences: `\n`, `\t`, `\r`, `\0`, `\b`, `\f`, `\\`, `\"`, `\'`, `\/`
and `\uXXXX`.

## Lists and dicts

```rex
rex.let fruits = ["banana", "apple"]
rex.push(fruits, "cherry")      # mutate in place
rex.show(fruits[0])             # banana
rex.show(fruits[-1])            # cherry   negative indexes count from the end

rex.let user = {"name": "Andile", "langs": ["Rex", "Python"]}
rex.show(user.name)
rex.show(user["langs"][1])
rex.show(rex.has(user, "email"))   # false
```

Reading a missing key is an error that lists the keys that do exist, which is
usually faster than debugging a silent `null`. Use `rex.has()` when a key is
optional.

Dict keys are strings; numeric keys are converted for you.

## Errors

Rex has one error type, raised by the language and by builtins. Catch it:

```rex
rex.try
  rex.let data = rex.get("https://example.com/missing")
rex.catch err
  rex.show(err.message)
  rex.show("at ${err.filename}:${err.line}")
rex.end
```

The caught value is a dict with `message`, `type`, `line`, `col` and `filename`.

Raise your own:

```rex
rex.throw "something went wrong"
rex.error("same thing, shorter")     # builtin form
rex.assert(rex.len(items) > 0, "no items to process")
```

`rex.try` catches Rex errors, including HTTP failures, missing files and type
errors. It does not swallow `rex.return`, `rex.break`, `rex.continue` or
`rex.exit`.

Every error renders with position and, where useful, a hint:

```
Rex Error: key 'title' not found
  hint: available keys: 'id', 'body'
  --> demo.rex:4:11
  |
4 | rex.show(post.title)
  |           ^
```

## Modules

`rex.import "path.rex"` runs another file in the current scope, so its functions
and variables become available to the importer. Paths are resolved relative to
the importing file, then the working directory.

```rex
# lib/greet.rex
rex.func greet(name)
  rex.return "Sawubona, ${name}!"
rex.end
```

```rex
# main.rex
rex.import "lib/greet.rex"
rex.show(greet("Mhlaba"))
```

Circular imports are detected and reported instead of looping forever.

## Limits

| Limit | Default | Flag |
|---|---|---|
| Statements executed | 5,000,000 | `--max-steps` |
| Nested function calls | 200 | `--max-depth` |

Hitting a limit is a normal Rex error, so a runaway loop reports
`execution limit reached` instead of freezing your terminal.

## Comments and style

```rex
# A whole-line comment
rex.let port = 8080   # and a trailing one
```

Two-space indentation, one statement per line, and `rex.end` on its own line is
the style used by every example in this repository.

## Grammar

The formal grammar lives in [the spec](spec.md).
