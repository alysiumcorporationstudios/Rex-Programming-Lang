# Examples

Fourteen programs live in [`examples/`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/tree/main/examples).
Each one is small enough to read in a minute and runs as-is.

| File | What it shows |
|---|---|
| [`hello.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/hello.rex) | the smallest program |
| [`variables.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/variables.rex) | values, reassignment, interpolation |
| [`control_flow.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/control_flow.rex) | if/elif/else, while, for, break, continue |
| [`functions.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/functions.rex) | defaults, recursion, closures |
| [`collections.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/collections.rex) | lists, dicts, sorting, aggregation |
| [`strings.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/strings.rex) | split, join, replace, escapes |
| [`json_tools.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/json_tools.rex) | parse, edit and re-serialise JSON |
| [`errors.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/errors.rex) | try/catch/throw/assert, including network failures |
| [`files.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/files.rex) | write, append, read, list |
| [`env_args.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/env_args.rex) | environment variables and CLI arguments |
| [`api_fetch.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/api_fetch.rex) | GET and read the response |
| [`api_crud.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/api_crud.rex) | POST, PUT, PATCH, DELETE, full responses |
| [`fizzbuzz.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/fizzbuzz.rex) | the classic |
| [`word_count.rex`](https://github.com/alysiumcorporationstudios/Rex-Programming-Lang/blob/main/examples/word_count.rex) | a small end-to-end report |

Run them all:

```bash
for f in examples/*.rex; do echo "== $f"; rex run "$f"; done
```

Or use `make examples`.

## A closer look: `word_count.rex`

```rex
rex.let text = "rex is tiny rex is friendly rex fetches json and prints it"

rex.let words = rex.split(rex.lower(text))
rex.let counts = {}

rex.for word in words
  rex.if rex.has(counts, word)
    counts[word] = counts[word] + 1
  rex.else
    counts[word] = 1
  rex.end
rex.end

rex.show("word counts:")
rex.for word in rex.keys(counts)
  rex.show(" ", word, "->", counts[word])
rex.end

rex.let unique_words = rex.unique(words)
rex.show("unique words:", rex.len(unique_words))
rex.show("longest word:", rex.sort(unique_words, true)[0])
```

```
word counts:
  rex -> 3
  is -> 2
  tiny -> 1
  friendly -> 1
  fetches -> 1
  json -> 1
  and -> 1
  prints -> 1
  it -> 1
unique words: 9
longest word: tiny
```

## A closer look: `api_crud.rex`

```rex
rex.let base = "https://jsonplaceholder.typicode.com/posts"

rex.let created = rex.post(base, {"title": "Rex post", "body": "hello", "userId": 1})
rex.show("created id:", created.id)

rex.let response = rex.request("GET", "${base}/1")
rex.show("status:", response.status, "ok:", response.ok)
rex.show("title:", response.json.title)
rex.show("content type:", response.headers["Content-Type"])
```

`rex.post` returns parsed JSON. `rex.request` returns the whole response:
`status`, `ok`, `headers`, `json`, `text` and `url`.
