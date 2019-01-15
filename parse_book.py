from ebooklib import epub


if __name__ == '__main__':
    book = epub.read_epub('books/stormlight_1/mobi8/stormlight_1.epub')
    print(book)


# algorithm notes:
# for each word in text, if word is in set of names (use dict??) then look up to 15 words
# forward in the text and increment the edge size for each pair of names that need to be
# associated.
