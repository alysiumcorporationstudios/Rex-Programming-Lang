# strings.rex — text handling
rex.let raw = "  Rex,Python,JavaScript  "
rex.let cleaned = rex.trim(raw)
rex.show("cleaned:", "[${cleaned}]")

rex.let langs = rex.split(cleaned, ",")
rex.show("languages:", langs)
rex.for lang in langs
  rex.show(" -", rex.upper(lang))
rex.end

rex.show("joined:", rex.join(langs, " | "))
rex.show("replaced:", rex.replace(cleaned, ",", " and "))
rex.show("starts with Rex:", rex.starts_with(cleaned, "Rex"))
rex.show("length:", rex.len(cleaned))
rex.show("repeat:", rex.repeat("=", 12))

# multi-line text keeps its escapes
rex.show("line one\nline two\ttabbed")
