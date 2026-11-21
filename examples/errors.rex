# errors.rex — rex.try / rex.catch / rex.throw / rex.assert
rex.func divide(a, b)
  rex.if b == 0
    rex.throw "cannot divide ${a} by zero"
  rex.end
  rex.return a / b
rex.end

rex.show("10 / 2 =", divide(10, 2))

rex.try
  rex.show(divide(1, 0))
rex.catch err
  rex.show("caught:", err.message)
  rex.show("where:", "${err.filename}:${err.line}")
rex.end

# a failing network call is catchable too
rex.try
  rex.get("https://this-host-does-not-exist.invalid/data")
rex.catch err
  rex.show("network problem handled:", err.message)
rex.end

rex.assert(divide(9, 3) == 3, "math is broken")
rex.show("assertions passed")
