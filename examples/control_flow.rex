# control_flow.rex — rex.if, rex.elif, rex.else, rex.while, rex.for
rex.let score = 82

rex.if score >= 90
  rex.show("grade A")
rex.elif score >= 75
  rex.show("grade B")
rex.elif score >= 60
  rex.show("grade C")
rex.else
  rex.show("keep going")
rex.end

# while loop
rex.let countdown = 3
rex.while countdown > 0
  rex.show("countdown", countdown)
  countdown = countdown - 1
rex.end

# for loop over a list
rex.for city in ["Johannesburg", "Durban", "Cape Town"]
  rex.show("city:", city)
rex.end

# for loop over a range, with break and continue
rex.for n in rex.range(1, 11)
  rex.if n % 2 == 0
    rex.continue
  rex.end
  rex.if n > 7
    rex.break
  rex.end
  rex.show("odd:", n)
rex.end

# loop over dict keys
rex.let stock = {"apples": 3, "pears": 5}
rex.for item in stock
  rex.show(item, "=", stock[item])
rex.end
