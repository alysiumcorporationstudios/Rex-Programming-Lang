# Standard library

Everything in Rex lives under the `rex` namespace, so a script never collides
with the language itself. This page is generated from the interpreter source by
`scripts/gen_stdlib_docs.py`, so it always matches the shipped behaviour.

```rex
rex.show("Sawubona")                                    # printing
rex.let post = rex.get("https://example.com/api/1")     # HTTP
rex.show(post.title)                                    # property access
rex.let slug = rex.replace(rex.lower(post.title), " ", "-")
rex.write("post.txt", rex.json.stringify(post, true))
```

## At a glance

| Group | Members |
|---|---|
| `rex` | `show`, `input`, `exit`, `error`, `env`, `get`, `post`, `put`, `patch`, `delete`, `request`, `read`, `write`, `append`, `exists`, `list_files`, `upper`, `lower`, `trim`, `split`, `join`, `replace`, `contains`, `starts_with`, `ends_with`, `repeat`, `len`, `push`, `pop`, `keys`, `values`, `has`, `range`, `sort`, `reverse`, `sum`, `first`, `last`, `unique`, `type`, `str`, `num`, `bool`, `clone`, `uuid`, `assert` |
| `rex.json` | `parse`, `stringify` |
| `rex.math` | `sqrt`, `floor`, `ceil`, `round`, `abs`, `pow`, `random`, `min`, `max` |
| `rex.time` | `now`, `timestamp`, `sleep` |

60 functions and 7 values.

## `rex`

| Function | Arguments | Description |
|---|---|---|
| `rex.show` | 0 or more | Print values to stdout. |
| `rex.input` | 0 to 1 | Read one line from stdin. |
| `rex.exit` | 0 to 1 | Stop the program with an exit code. |
| `rex.error` | 0 to 1 | Raise a runtime error. |
| `rex.env` | 1 to 2 | Read an environment variable. |
| `rex.get` | 1 to 2 | HTTP GET, returns parsed JSON or text. |
| `rex.post` | 1 to 3 | HTTP POST with a JSON body. |
| `rex.put` | 1 to 3 | HTTP PUT with a JSON body. |
| `rex.patch` | 1 to 3 | HTTP PATCH with a JSON body. |
| `rex.delete` | 1 to 2 | HTTP DELETE. |
| `rex.request` | 2 to 3 | Full HTTP response as a dict. |
| `rex.read` | 1 | Read a UTF-8 file. |
| `rex.write` | 2 | Write a UTF-8 file. |
| `rex.append` | 2 | Append to a UTF-8 file. |
| `rex.exists` | 1 | True when a path exists. |
| `rex.list_files` | 0 to 1 | Names inside a directory. |
| `rex.upper` | 1 | Uppercase a string. |
| `rex.lower` | 1 | Lowercase a string. |
| `rex.trim` | 1 | Strip surrounding whitespace. |
| `rex.split` | 1 to 2 | Split a string into a list. |
| `rex.join` | 1 to 2 | Join a list into a string. |
| `rex.replace` | 3 | Replace every occurrence of a substring. |
| `rex.contains` | 2 | Membership test for strings, lists and dicts. |
| `rex.starts_with` | 2 | Prefix test. |
| `rex.ends_with` | 2 | Suffix test. |
| `rex.repeat` | 2 | Repeat a string n times. |
| `rex.len` | 1 | Length of a string, list or dict. |
| `rex.push` | 2 or more | Append items to a list. |
| `rex.pop` | 1 to 2 | Remove and return a list item. |
| `rex.keys` | 1 | Keys of a dict. |
| `rex.values` | 1 | Values of a dict. |
| `rex.has` | 2 | True when a key or index exists. |
| `rex.range` | 1 to 3 | List of numbers. |
| `rex.sort` | 1 to 2 | Sorted copy of a list. |
| `rex.reverse` | 1 | Reversed copy of a list or string. |
| `rex.sum` | 1 | Sum of a list of numbers. |
| `rex.first` | 1 | First item of a list. |
| `rex.last` | 1 | Last item of a list. |
| `rex.unique` | 1 | De-duplicated copy of a list. |
| `rex.type` | 1 | Rex type name of a value. |
| `rex.str` | 0 to 1 | Convert a value to a string. |
| `rex.num` | 0 to 1 | Convert a value to a number. |
| `rex.bool` | 0 to 1 | Convert a value to a boolean. |
| `rex.clone` | 1 | Deep copy of a list or dict. |
| `rex.uuid` | 0 | Random UUID v4 string. |
| `rex.assert` | 1 to 2 | Fail unless the condition is truthy. |

## `rex.json`

| Function | Arguments | Description |
|---|---|---|
| `rex.json.parse` | 1 | Parse a JSON string. |
| `rex.json.stringify` | 0 to 2 | Serialise a value to JSON. |

## `rex.math`

| Function | Arguments | Description |
|---|---|---|
| `rex.math.sqrt` | 1 | Square root. |
| `rex.math.floor` | 1 | Round down. |
| `rex.math.ceil` | 1 | Round up. |
| `rex.math.round` | 1 to 2 | Round to n digits. |
| `rex.math.abs` | 1 | Absolute value. |
| `rex.math.pow` | 2 | Raise to a power. |
| `rex.math.random` | 0 | Random number in [0, 1). |
| `rex.math.min` | 1 or more | Smallest number. |
| `rex.math.max` | 1 or more | Largest number. |

## `rex.time`

| Function | Arguments | Description |
|---|---|---|
| `rex.time.now` | 0 | Current UTC time as ISO 8601. |
| `rex.time.timestamp` | 0 | Seconds since the epoch. |
| `rex.time.sleep` | 1 | Pause for n seconds. |

## Values

- `rex.json` = `{'parse': <builtin rex.json.parse>, 'stringify': <builtin rex.json.stringify>}`
- `rex.time` = `{'now': <builtin rex.time.now>, 'timestamp': <builtin rex.time.timestamp>, 'sleep': <builtin rex.time.sleep>}`
- `rex.math` = `{'sqrt': <builtin rex.math.sqrt>, 'floor': <builtin rex.math.floor>, 'ceil': <builtin rex.math.ceil>, 'round': <builtin rex.math.round>, 'abs': <builtin rex.math.abs>, 'pow': <builtin rex.math.pow>, 'random': <builtin rex.math.random>, 'min': <builtin rex.math.min>, 'max': <builtin rex.math.max>, 'pi': 3.141592653589793, 'e': 2.718281828459045}`
- `rex.math.pi` = `3.141592653589793`
- `rex.math.e` = `2.718281828459045`
- `rex.args` = `[]`
- `rex.version` = `1.0.0`

## Behaviour worth knowing

- **Numbers** are integers or floats. Division always produces a float;
  `rex.math.round(x)` returns an integer when you ask for 0 digits.
- **Strings** support `${...}` interpolation in double quotes only. Single
  quotes are literal.
- **Truthiness**: `null`, `false`, `0`, `0.0`, `""`, `[]` and `{}` are false;
  everything else is true.
- **Equality** is structural and type aware, so `1 == true` is `false`.
- **HTTP** builtins return parsed JSON when the response is JSON, otherwise the
  response text. Use `rex.request()` when you need the status code or headers.
- **HTTP errors** are catchable Rex errors: a 404 raises, so wrap calls in
  `rex.try` / `rex.catch` when a missing resource is expected.
- **Files** are read and written as UTF-8. `rex.write` creates parent
  directories for you.
- **Copies vs mutation**: `rex.sort`, `rex.reverse`, `rex.unique` and
  `rex.clone` return copies. `rex.push` and `rex.pop` mutate in place, which is
  what you want inside a loop.
