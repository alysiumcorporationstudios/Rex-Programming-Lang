# fizzbuzz.rex — the classic, in Rex
rex.for n in rex.range(1, 21)
  rex.if n % 15 == 0
    rex.show("FizzBuzz")
  rex.elif n % 3 == 0
    rex.show("Fizz")
  rex.elif n % 5 == 0
    rex.show("Buzz")
  rex.else
    rex.show(n)
  rex.end
rex.end
