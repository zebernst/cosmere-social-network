import yaml

from core.characters import Character, characters_
from core.constants import book_keys, titles, worlds
from utils.epub import chapters
from utils.logs import create_logger
from utils.paths import disambiguation_dir


# todo: add logging
logger = create_logger('csn.core.disambiguation')


# todo: split name identification in runs into separate file, divorce from disambiguation

def clarify_REFACTORME(name: str, names: dict, line: str):
    # todo: check character's .books attribute against current processing key

    local_chars = [c for c in names[name] if any(b == key.split('/')[0] for b in c.books)]
    if len(local_chars) == 1:
        logger.debug(f'Automatically matched ambiguous character {repr(local_chars[0])} from {name} -- '
                     f'only character with presence in {key}')
        return local_chars[0]

    print(f'Ambiguous reference found for `{name}`! Please choose the correct character that '
          f'appears in the following run:')
    print(line)
    for i2, name2 in enumerate(names[name]):
        print(f"  {i2 + 1}: {name2.name} ({name2.world}) -- {name2.info}")
    print("  o: The character is not listed.")
    print("  x: This is not a character.")
    response = input("> ")
    while not ((response.isdigit() and int(response) <= len(names[name]))
               or response.lower().startswith('x')
               or response.lower().startswith('o')):
        response = input("> ")
    if response.startswith('x'):
        return None
    if response.startswith('o'):
        response = input("Type the name of the character the keyword is referring to: ")
        while response not in names:
            response = input("Character not found. Try again: ")

        if isinstance(names[response], list):
            # todo: clean up recursive calls
            ch = clarify_REFACTORME(response, names, line)
        else:
            ch = names[response]
    else:
        idx2 = int(response) - 1
        ch = names[name][idx2]

    logger.debug(f'Manually matched ambiguous character {repr(ch)}.')
    return ch


def verify(key: str, ch: Character, word: str):
    belongs = any(b == key.split('/')[0] for b in ch.books)
    if not belongs:
        logger.debug(f'Ignoring potential match of {repr(ch)} from "{word}" - character does not appear in {key}')
    return belongs


if __name__ == '__main__':
    characters = list(characters_)

    monikers = {}
    for c in characters:
        for name in c.monikers:
            if name in monikers:
                if isinstance(monikers[name], Character):
                    monikers[name] = [monikers[name], c]
                elif isinstance(monikers[name], list):
                    monikers[name].append(c)
            else:
                monikers[name] = c

    char_ids = {c.id: c for c in characters}

    for key in book_keys:
        if key != 'mistborn/era2/bands-of-mourning':
            continue

        world = worlds.get(key)

        with (disambiguation_dir / key).with_suffix('.yml').open(mode='r') as f:
            disambiguation = yaml.load(f, yaml.Loader)
            if disambiguation is None:
                disambiguation = {}

        for chapter, tokens in chapters(key):
            run_size = 25
            idx = 0

            if chapter not in disambiguation:
                disambiguation[chapter] = {}

            while idx < len(tokens):
                local_tokens = tokens[idx:idx + run_size]
                run = ' '.join(local_tokens).strip()

                chars = []
                i = 0
                while i < len(local_tokens):
                    name = local_tokens[i]
                    full_name = ' '.join(local_tokens[i:i + 2])
                    char: Character = None

                    if full_name in monikers:
                        if isinstance(monikers[full_name], list):
                            if idx + i in disambiguation[chapter]:
                                char_id = disambiguation[chapter][idx + i]
                                char = char_ids[char_id] if char_id is not None else None
                            else:
                                char = clarify_REFACTORME(full_name, monikers, run)
                                disambiguation[chapter][idx + i] = char.id if char else None
                        else:
                            char = monikers[full_name] if verify(key, monikers[full_name], full_name) else None
                        i += 2

                    elif full_name not in monikers and name in titles:
                        i += 1
                        continue

                    elif name in monikers:
                        if isinstance(monikers[name], list):
                            if idx + i in disambiguation[chapter]:
                                char_id = disambiguation[chapter][idx + i]
                                char = char_ids[char_id] if char_id is not None else None
                            else:
                                char = clarify_REFACTORME(name, monikers, run)
                                disambiguation[chapter][idx + i] = char.id if char else None
                        else:
                            char = monikers[name] if verify(key, monikers[name], name) else None
                        i += 1

                    else:
                        i += 1
                        continue

                    # todo: advance by two tokens if possible, else fall back to one

                    # todo: disambiguation stores word, resolved character, and position, checks if resolved
                    #       word exists within length of last run

                    if char is not None:
                        # if not verify(key, char):
                        #     char = None
                        if char.world.lower() != world and 'worldhopping' not in char.abilities:
                            if idx + i not in disambiguation[chapter]:
                                print(f"Non-native non-worldhopping character found! Please confirm presence "
                                      f"of {char.name} (from {char.world}) in the following run:")
                                print(run)
                                disambiguation[chapter][idx + i] = input(">  character present? y/n: ").lower().startswith('y')
                            elif disambiguation[chapter][idx + i]:
                                chars.append((i, char))
                        else:
                            chars.append((i, char))

                # advance past first found character
                if len(chars) >= 2:
                    idx += chars[0][0] + 1
                    print(f"{run:200s} // {chars}")

                # advance until only character is at beginning of run (max threshold)
                elif len(chars) == 1:
                    idx += chars[0][0] if chars[0][0] > 0 else 1
                    print(f"{run:200s} // {chars}")

                # skip run if no chars found
                else:
                    idx += run_size - 1
                    print(f"{run:200s} // {chars}")

            with (disambiguation_dir / key).with_suffix('.yml').open(mode='w') as f:
                yaml.dump(disambiguation, f, yaml.Dumper, default_flow_style=False, sort_keys=False)
