from typing import Optional

import colorama

from core.characters import Character, characters_
from utils.input import ask, menu, yn_question
from utils.logs import create_logger


# todo: add logging
logger = create_logger('csn.core.disambiguation')

_characters = list(characters_)
_char_ids = {c.id: c for c in _characters}
monikers = {}
for c in _characters:
    for one in c.monikers:
        if one in monikers:
            if isinstance(monikers[one], Character):
                monikers[one] = [monikers[one], c]
            elif isinstance(monikers[one], list):
                monikers[one].append(c)
        else:
            monikers[one] = c


def char_search(prompt: Optional[str]) -> Optional[Character]:
    response = ask(prompt=prompt,
                   validator=lambda r: r in monikers,
                   error="Character not found.")

    if response is None:
        exit(1)

    if isinstance(monikers[response], list):
        print(f"Multiple matches found for {response}. Please specify:")
        for c in monikers[response]:
            print(f"  {c.name} ({c.world}) -- {c.info}")
        return char_search(prompt=None)
    else:
        return monikers[response]


def clarify_list(key: str, name: str, names: dict):

    local_chars = [c for c in names[name] if verify_presence(key, c, name)]
    if not local_chars:
        return None

    if len(local_chars) == 1:
        logger.debug(f'Match of ambiguous character confirmed automatically -- "{name}" identified as '
                     f'{repr(local_chars[0])} with presence in {key}.')
        return local_chars[0]

    response = menu(prompt=f'Ambiguous reference found for "{name}"! Please choose the correct character.',
                    options=[f"  {i+1}: {c.name} ({c.world}) -- {c.info}" for i, c in enumerate(local_chars)]
                          + [f"  o: The correct character is not listed.",
                             f"  x: This is not a character."],
                    validator=lambda r: (r.isdigit() and int(r) <= len(local_chars))
                                        or r.lower().startswith('x')
                                        or r.lower().startswith('o'))

    if response.startswith('x'):
        return None
    elif response.startswith('o'):
        ch = char_search("Type the name of the character the keyword is referring to: ")
        logger.debug(f'Match of ambiguous character confirmed manually      -- "{name}" identified as {repr(ch)}.')
        return ch
    else:
        ch = names[name][int(response) - 1]
        logger.debug(f'Match of ambiguous character confirmed from list     -- "{name}" identified as {repr(ch)}.')
        return ch


def verify_presence(key: str, ch: Character, word: str):
    in_book = any(b == key.split('/')[0] for b in ch.books)
    if not in_book:
        logger.debug(f'Match of ambiguous character rejected  automatically -- "{word}" identified as '
                     f'{repr(ch)} does not appear in {key}.')
    return in_book


def save(pos: int, char: Optional[Character], disambiguation: dict) -> None:
    disambiguation[pos] = char.id if char is not None else None


def recall(pos: int, disambiguation: dict) -> Optional[Character]:
    return _char_ids.get(disambiguation.get(pos), None)


def disambiguate_name(key: str, name: str, disambiguation: dict, pos: int, context: list) -> Optional[Character]:
    if pos in disambiguation:
        char = recall(pos, disambiguation)
        if char is not None:
            logger.debug(f'Match of ambiguous character confirmed automatically -- '
                         f'{repr(char)} found in disambiguation.')
        return char

    else:
        print(colorama.Fore.LIGHTBLACK_EX + '\n'.join(context[:-1]))
        print(colorama.Style.BRIGHT + context[-1])
        char = clarify_list(key, name, monikers)
        save(pos, char, disambiguation)
        return char


def disambiguate_title(title: str, disambiguation: dict, pos: int, context: list) -> Optional[Character]:
    if pos in disambiguation:
        char = recall(pos, disambiguation)
        if char is not None:
            logger.debug(f'Match of ambiguous character confirmed automatically -- '
                         f'{repr(char)} found in disambiguation.')
        return char

    else:
        print(colorama.Fore.LIGHTBLACK_EX + '\n'.join(context[:-1]))
        print(colorama.Style.BRIGHT + context[-1])
        if yn_question(f'Ambiguous reference found for "{title}". '
                       f'Does this refer to a character?'):
            char = char_search(f"Who does this refer to?")
            save(pos, char, disambiguation)
        else:
            char = None
            save(pos, None, disambiguation)
        if char is not None:
            logger.debug(f'Match of ambiguous character confirmed manually      -- "{title}" identified as {repr(char)}.')
        return char
