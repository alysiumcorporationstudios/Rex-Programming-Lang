# api_fetch.rex — the reason Rex exists: fetch JSON and read it
# needs: internet access
rex.show("Rex API fetch demo")

rex.let url = "https://jsonplaceholder.typicode.com/posts/1"
rex.let post = rex.get(url)

rex.show("title:", post.title)
rex.show("author id:", post.userId)
rex.show(post)
