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
import yaml

from core.characters import Character
from core.constants import book_keys, titles, worlds
from core.disambiguation import disambiguate_name, disambiguate_title, monikers, verify_presence
from utils.epub import chapters
from utils.paths import disambiguation_dir


for book in book_keys:
    if book != 'mistborn/era2/bands-of-mourning':
        continue

    world = worlds.get(book)

    with (disambiguation_dir / book).with_suffix('.yml').open(mode='r') as f:
        disambiguation = yaml.load(f, yaml.Loader)
        if disambiguation is None:
            disambiguation = {}

    for chapter, tokens in chapters(book):
        run_size = 25
        idx = 0

        if chapter not in disambiguation:
            disambiguation[chapter] = {}

        while idx < len(tokens):
            local_tokens = tokens[idx:idx + run_size]
            context = [' '.join(tokens[idx-(i*run_size):idx-((i-1)*run_size)]).strip() for i in range(4, -1, -1)]

            chars = []
            i = 0
            while i < len(local_tokens):
                char: Character = None
                pos = idx + i

                this_token = local_tokens[i]
                next_token = local_tokens[i+1] if i+1 < len(local_tokens) else ''
                third_token = local_tokens[i + 2] if i + 2 < len(local_tokens) else ''
                two_tokens = this_token + ' ' + next_token
                next_two_tokens = next_token + ' ' + third_token
                three_tokens = two_tokens + ' ' + third_token

                if three_tokens in monikers:
                    if isinstance(monikers[three_tokens], list):
                        char = disambiguate_name(book, three_tokens, disambiguation[chapter], pos, context)
                    else:
                        char = monikers[three_tokens] if verify_presence(book, monikers[three_tokens], three_tokens) else None

                    i += 3

                elif two_tokens in monikers:
                    if isinstance(monikers[two_tokens], list):
                        char = disambiguate_name(book, two_tokens, disambiguation[chapter], pos, context)
                    else:
                        char = monikers[two_tokens] if verify_presence(book, monikers[two_tokens], two_tokens) else None

                    i += 2

                elif this_token in titles:
                    if next_token not in monikers and next_two_tokens not in monikers:
                        char = disambiguate_title(this_token, disambiguation[chapter], pos, context)
                    i += 1

                elif this_token in monikers:
                    if isinstance(monikers[this_token], list):
                        char = disambiguate_name(book, this_token, disambiguation[chapter], pos, context)
                    else:
                        char = monikers[this_token] if verify_presence(book, monikers[this_token], this_token) else None

                    i += 1

                else:
                    i += 1
                    continue

                if char is not None:
                    chars.append((i, char))

            # advance past first found character
            if len(chars) >= 2:
                idx += chars[0][0] + 1

            # advance until only character is at beginning of run (max threshold)
            elif len(chars) == 1:
                idx += chars[0][0] if chars[0][0] > 0 else 1

            # skip run if no chars found
            else:
                idx += run_size - 1

            characters = set(c for i, c in chars)
            if len(characters) > 1:
                print(characters)

        with (disambiguation_dir / book).with_suffix('.yml').open(mode='w') as f:
            yaml.dump(disambiguation, f, yaml.Dumper, default_flow_style=False, sort_keys=False)
