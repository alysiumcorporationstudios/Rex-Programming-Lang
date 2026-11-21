# api_crud.rex — POST, PUT, PATCH, DELETE and full responses
# needs: internet access
rex.let base = "https://jsonplaceholder.typicode.com/posts"

rex.let created = rex.post(base, {"title": "Rex post", "body": "hello", "userId": 1})
rex.show("created id:", created.id)

rex.let updated = rex.put("${base}/1", {"id": 1, "title": "updated", "userId": 1})
rex.show("updated title:", updated.title)

rex.let patched = rex.patch("${base}/1", {"title": "patched"})
rex.show("patched title:", patched.title)

rex.let response = rex.request("GET", "${base}/1")
rex.show("status:", response.status, "ok:", response.ok)
rex.show("title:", response.json.title)
rex.show("content type:", response.headers["Content-Type"])

rex.delete("${base}/1")
rex.show("deleted 1")
