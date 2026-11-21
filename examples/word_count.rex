# word_count.rex — a small text report, end to end
rex.let text = "rex is tiny rex is friendly rex fetches json and prints it"

rex.let words = rex.split(rex.lower(text))
rex.let counts = {}

rex.for word in words
  rex.if rex.has(counts, word)
    counts[word] = counts[word] + 1
  rex.else
    counts[word] = 1
  rex.end
rex.end

rex.show("word counts:")
rex.for word in rex.keys(counts)
  rex.show(" ", word, "->", counts[word])
rex.end

rex.let unique_words = rex.unique(words)
rex.show("unique words:", rex.len(unique_words))
rex.show("longest word:", rex.sort(unique_words, true)[0])
