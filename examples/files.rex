# files.rex — reading and writing text files
rex.let path = "rex_notes.txt"

rex.write(path, "first line\n")
rex.append(path, "second line\n")
rex.show("exists:", rex.exists(path))

rex.let content = rex.read(path)
rex.show("file contains:")
rex.show(rex.trim(content))

rex.for line in rex.split(rex.trim(content), "\n")
  rex.show("line:", line)
rex.end

rex.show("files here:", rex.list_files("."))
