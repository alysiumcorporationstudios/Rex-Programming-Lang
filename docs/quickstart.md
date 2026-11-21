# Quick start

## Hello, Mzansi

Create `hello.rex`:

```rex
rex.show("Sawubona Mhlaba")
```

Run it:

```bash
rex run hello.rex
```

```
Sawubona Mhlaba
```

`rex hello.rex` does the same thing. `rex run` also accepts flags and passes
everything after the file to your script as `rex.args`.

## Talk to an API

```rex
rex.let url = "https://jsonplaceholder.typicode.com/posts/1"
rex.let post = rex.get(url)

rex.show(post.title)
rex.show(post.userId)
```

`rex.get` returns parsed JSON, so `post.title` just works. Objects and lists are
pretty-printed when you `rex.show` them:

```rex
rex.show(post)
```

```
{
  "userId": 1,
  "id": 1,
  "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
  "body": "quia et suscipit\nsuscipit recusandae consequuntur expedita et cum..."
}
```

## Add logic

```rex
rex.let score = 82

rex.if score >= 90
  rex.show("grade A")
rex.elif score >= 75
  rex.show("grade B")
rex.else
  rex.show("keep going")
rex.end
```

Every block ends with `rex.end`. That is the whole rule: no indentation rules to
break, no braces to count.

## Loop

```rex
rex.for n in rex.range(1, 6)
  rex.show("step", n)
rex.end
```

`rex.for` walks lists, strings and dict keys. `rex.range` gives you numbers.

## Write a function

```rex
rex.func total(prices)
  rex.let sum = 0
  rex.for price in prices
    sum = sum + price
  rex.end
  rex.return sum
rex.end

rex.show("total:", total([19.99, 5.00, 12.50]))
```

## Handle failure

Network calls fail. Wrap them:

```rex
rex.try
  rex.let data = rex.get("https://httpbin.org/status/404")
rex.catch err
  rex.show("failed:", err.message)
rex.end
```

```
failed: HTTP 404 for GET https://httpbin.org/status/404
```

## Next steps

- [Language reference](language.md): every statement, operator and rule.
- [Standard library](stdlib.md): all 60 builtins.
- [Examples](examples.md): 14 runnable programs, from fizzbuzz to a text report.
- [CLI](cli.md): `run`, `repl`, `check`, `ast`, `init`.
