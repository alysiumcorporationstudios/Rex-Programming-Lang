# json_tools.rex — parse, inspect and build JSON
rex.let text = '{"team": "Alysium", "members": 3, "stack": ["Rex", "Python"]}'

rex.let data = rex.json.parse(text)
rex.show("team:", data.team)
rex.show("stack size:", rex.len(data.stack))

rex.push(data.stack, "JavaScript")
data.members = data.members + 1

rex.show("pretty:")
rex.show(rex.json.stringify(data, true))

rex.show("compact:", rex.json.stringify(data))

rex.let round_trip = rex.json.parse(rex.json.stringify(data))
rex.show("round trip equal:", round_trip.team == data.team)
