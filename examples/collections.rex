# collections.rex — lists and dicts, the bread and butter of API work
rex.let fruits = ["banana", "apple", "cherry"]
rex.push(fruits, "date")
rex.show("count:", rex.len(fruits))
rex.show("sorted:", rex.sort(fruits))
rex.show("reversed:", rex.reverse(fruits))
rex.show("first:", rex.first(fruits), "last:", rex.last(fruits))
rex.show("has apple:", rex.contains(fruits, "apple"))

rex.let user = {
  "name": "Andile",
  "role": "developer",
  "langs": ["Rex", "Python"]
}

rex.show("keys:", rex.keys(user))
rex.show("name:", user.name)
rex.show("second language:", user.langs[1])
rex.show("has email:", rex.has(user, "email"))

# update a nested value
user.role = "maintainer"
user["country"] = "South Africa"
rex.show(user)

rex.let scores = [42, 7, 19, 88]
rex.show("sum:", rex.sum(scores))
rex.show("max:", rex.math.max(scores))
rex.show("average:", rex.math.round(rex.sum(scores) / rex.len(scores), 2))
