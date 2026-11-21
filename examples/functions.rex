# functions.rex — rex.func, defaults, recursion and closures
rex.func greet(who, greeting = "Sawubona")
  rex.return "${greeting}, ${who}!"
rex.end

rex.show(greet("Mhlaba"))
rex.show(greet("Andile", "Hello"))

rex.func factorial(n)
  rex.if n <= 1
    rex.return 1
  rex.end
  rex.return n * factorial(n - 1)
rex.end

rex.show("10! =", factorial(10))

rex.func fib(n)
  rex.if n < 2
    rex.return n
  rex.end
  rex.return fib(n - 1) + fib(n - 2)
rex.end

rex.let series = []
rex.for i in rex.range(0, 10)
  rex.push(series, fib(i))
rex.end
rex.show("fibonacci:", series)

# functions are values, and closures remember their scope
rex.func make_counter()
  rex.let total = 0
  rex.func bump(step = 1)
    total = total + step
    rex.return total
  rex.end
  rex.return bump
rex.end

rex.let counter = make_counter()
rex.show(counter(), counter(5), counter(2))
