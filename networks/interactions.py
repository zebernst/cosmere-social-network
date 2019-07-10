##### algorithm notes #####

# for each word in text, if word is in set of names (use dict??) then look up to 15 words
# forward in the text and increment the edge size for each pair of names that need to be
# associated.

# use a modified multidictionary with {moniker: [chars]} to indicate any clashes in names
# (notably surnames) and ask the user to clarify which character it is. use this data structure
# in the disambiguation process to give the user options which names to pick from

# at least semi-automate process (narrow down title (king, etc) by world, but ask user to
# be certain rather than assuming wrong.

# also use up to 30 words at a time (advance by 5?) and compare indices in a modified
# queue to make sure that there are no duplicate instances of conversation being counted

# use techniques from comp261 when designing the algorithm. keep track of offset from beginning
# of string to first name found and use that to advance forward.

# make a dictionary that stores name position -> disambiguated character name whenever ambiguous
# names are found and user input is required. make disambiguation a cli task. this will allow
# processing of the source text independent of the format that it comes in - epub, mobi, html, txt, etc

# make this file (interactions.py) rely on a saved datastructure or use a dispatchable method to fetch
# the data, to enable divorcing of analysis from source material and allowing user to specify which
# kind they have.
