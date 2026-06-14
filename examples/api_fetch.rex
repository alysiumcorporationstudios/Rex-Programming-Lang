rex.show("Rex API fetch demo")
rex.let res = rex.get("https://jsonplaceholder.typicode.com/posts/1")
rex.show(res.title)
rex.show(res.userId)
rex.return
