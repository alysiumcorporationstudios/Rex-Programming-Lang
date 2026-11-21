# variables.rex — values, reassignment and string interpolation
rex.let name = "Andile"
rex.let year = 2026
rex.let language = "Rex"

rex.show(name)
rex.show(year)
rex.show("${language} was born in ${year}")

# variables can be reassigned without re-declaring
year = year + 1
rex.show("next year:", year)

rex.let pi = 3.14159
rex.let flag = true
rex.let nothing = null
rex.show(pi, flag, nothing)
rex.show(rex.type(pi), rex.type(flag), rex.type(nothing))
