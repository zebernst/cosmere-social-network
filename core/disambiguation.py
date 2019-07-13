from typing import Optional

import colorama

from core.characters import Character, characters, monikers
from utils.input import ask, menu, yn_question, clear_screen
from utils.logs import create_logger
from utils.simpletypes import RunContext


colorama.init(autoreset=True)
logger = create_logger('csn.core.disambiguation')

_char_ids = {c.id: c for c in characters}


def _save(pos: int, char: Optional[Character], disambiguation: dict) -> None:
    disambiguation[pos] = char.id if char is not None else None


def _recall(pos: int, disambiguation: dict) -> Optional[Character]:
    return _char_ids.get(disambiguation.get(pos), None)


def char_search(prompt: Optional[str]) -> Optional[Character]:
    response = ask(prompt=prompt,
                   validator=lambda r: r in monikers,
                   error="Character not found.")

    if response is None:
        exit(1)

    if isinstance(monikers[response], list):
        for char in monikers[response]:
            if char.name == response:
                return char
        print(f"Multiple matches found for {response}. Please specify:")
        for c in monikers[response]:
            print(f"  {c.name} ({c.world}) -- {c.info}")
        return char_search(prompt=None)
    else:
        return monikers[response]


def clarify_list(name: str, matches: list):
    response = menu(prompt=f'Ambiguous reference found for "{name}"! Please choose the correct character.',
                    options=[f"  {i+1}: {c.name} ({c.world}) -- {c.info}" for i, c in enumerate(matches)]
                          + [f"  o: The correct character is not listed.",
                             f"  x: This is not a character."],
                    validator=lambda r: (r.isdigit() and int(r) <= len(matches))
                                        or r.lower().startswith('x')
                                        or r.lower().startswith('o'))

    if response.startswith('x'):
        return None
    elif response.startswith('o'):
        ch = char_search("Type the name of the character the keyword is referring to: ")
        logger.debug(f'Matched ambiguous character from "{name}", identified manually as {repr(ch)}.')
        return ch
    else:
        ch = matches[int(response) - 1]
        logger.debug(f'Matched ambiguous character from "{name}", identified from list as {repr(ch)}.')
        return ch


def verify_presence(key: str, ch: Character, word: str):
    in_book = any(b == key.split('/')[0] for b in ch.books)
    if not in_book:
        logger.debug(f'Rejected ambiguous character from "{word}", identified automatically as '
                     f'{repr(ch)} who does not appear in {key}.')
    return in_book


def filter_present(key: str, name: str):
    local_chars = [c for c in monikers[name] if verify_presence(key, c, name)]
    return local_chars if local_chars is not None else None


def disambiguate_name(key: str, name: str, disambiguation: dict, pos: int, context: RunContext) -> Optional[Character]:
    if pos in disambiguation:
        char = _recall(pos, disambiguation)
        if char is not None:
            logger.debug(f'Matched ambiguous character from disambiguation, identified automatically as {repr(char)}.')
        return char

    else:
        local = filter_present(key, name)
        if len(local) == 1:
            char = local[0]
            logger.debug(f'Matched ambiguous character from "{name}", identified automatically as '
                         f'{repr(char)} with presence in {key}.')
        else:
            print(colorama.Fore.LIGHTBLACK_EX + '\n'.join(context.prev))
            print(colorama.Style.BRIGHT + context.run)
            print(colorama.Fore.LIGHTBLACK_EX + '\n'.join(context.next))
            char = clarify_list(name, local)
            clear_screen()

        _save(pos, char, disambiguation)
        return char


def disambiguate_title(title: str, disambiguation: dict, pos: int, context: RunContext) -> Optional[Character]:
    if pos in disambiguation:
        char = _recall(pos, disambiguation)
        if char is not None:
            logger.debug(f'Matched ambiguous character from disambiguation, identified automatically as {repr(char)}.')

        return char

    else:
        print(colorama.Fore.LIGHTBLACK_EX + '\n'.join(context.prev))
        print(colorama.Style.BRIGHT + context.run)
        print(colorama.Fore.LIGHTBLACK_EX + '\n'.join(context.next))

        if yn_question(f'Ambiguous reference found for "{title}". '
                       f'Does this refer to a character?'):
            char = char_search(f"Who does this refer to?")
        else:
            char = None

        clear_screen()
        if char is not None:
            logger.debug(f'Matched ambiguous character from "{title}", identified manually as {repr(char)}.')

        _save(pos, char, disambiguation)
        return char
