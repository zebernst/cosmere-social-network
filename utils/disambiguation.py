from typing import Optional, List

import colorama
import yaml
from tqdm import tqdm

from core.characters import Character, characters, lookup
from core.config import InteractionNetworkConfig
import utils.constants as constants
from utils.epub import tokenize_chapters
from utils.exceptions import AmbiguousReferenceError
from utils.paths import disambiguation_dir
from .input import ask, clear_screen, menu, yn_question
from .logs import get_logger
from .simpletypes import RunContext


__all__ = ['verify_presence', 'check_position', 'disambiguate_book']

RUN_SIZE = InteractionNetworkConfig.run_size
PREV_LINES = InteractionNetworkConfig.prev_cxt_lines
NEXT_LINES = InteractionNetworkConfig.next_cxt_lines

colorama.init(autoreset=True)
logger = get_logger('csn.core.disambiguation')

_char_ids = {c.id: c for c in characters}


def _save(pos: int, char: Optional[Character], disambiguation: dict) -> None:
    disambiguation[pos] = char.id if char is not None else None


def _recall(pos: int, disambiguation: dict) -> Optional[Character]:
    return _char_ids.get(disambiguation.get(pos), None)


def char_search(prompt: Optional[str]) -> Optional[Character]:
    response = ask(prompt=prompt,
                   validator=lambda r: slice(r, None) in lookup,
                   error="Character not found.")

    if response is None:
        exit(1)

    if response in lookup:
        matches = lookup[response]
    else:
        matches = lookup[response:]

    if len(matches) > 1:
        for char in matches:
            if char.name == response:
                return char
        print(f"Multiple matches found for {response}. Please specify:")
        for c in matches:
            print(f"  {c.details}")
        return char_search(prompt=None)
    else:
        return matches[0]


def clarify_list(name: str, matches: list, context: RunContext, pos: int) -> Optional[Character]:
    response = menu(prompt=f'Ambiguous reference found for "{name}"! Please choose the correct character.',
                    options=[f"  {i + 1}: {c.details}" for i, c in enumerate(matches)]
                            + [f"  o: The correct character is not listed.",
                               f"  x: This is not a character."],
                    validator=lambda r: (r.isdigit() and int(r) <= len(matches))
                                        or r.lower().startswith('x')
                                        or r.lower().startswith('o'))

    if response.startswith('x'):
        return None
    elif response.startswith('o'):
        ch = char_search("Type the name of the character the keyword is referring to: ")
        logger.debug(f'Matched ambiguous reference from "{name}" at {context.chapter}:{pos}, '
                     f'identified manually as {repr(ch)}.')
        return ch
    else:
        ch = matches[int(response) - 1]
        logger.debug(f'Matched ambiguous reference from "{name}" at {context.chapter}:{pos}, '
                     f'identified from list as {repr(ch)}.')
        return ch


def verify_presence(key: str, ch: Character, word: str) -> bool:
    in_book = any(b == key.split('/')[0] for b in ch.books)
    if not in_book:
        logger.debug(f'Rejected ambiguous reference from "{word}", identified automatically as '
                     f'{repr(ch)} who does not appear in {key}.')
    return in_book


def filter_present(key: str, name: str) -> List[Character]:
    return [c for c in lookup[name] if verify_presence(key, c, name)]


def disambiguate_name(key: str, name: str, disambiguation: dict, pos: int, context: RunContext) -> Optional[Character]:
    if pos in disambiguation:
        char = _recall(pos, disambiguation)
        if char is not None:
            logger.debug(f'Matched ambiguous reference using disambiguation, identified automatically as {repr(char)}.')
        return char

    else:
        save = False
        local = filter_present(key, name)
        if len(local) == 1:
            char = local[0]
            logger.debug(f'Matched ambiguous reference from "{name}" at {context.chapter}:{pos}, '
                         f'identified automatically as {repr(char)} with presence in {key}.')
        elif len(local) > 1:
            save = True
            print(colorama.Fore.LIGHTBLACK_EX + '\n'.join(context.prev))
            print(colorama.Style.BRIGHT + context.run)
            print(colorama.Fore.LIGHTBLACK_EX + '\n'.join(context.next))
            char = clarify_list(name, local, context, pos)
            clear_screen()
        else:
            char = None

        if save:
            _save(pos, char, disambiguation)
        return char


def disambiguate_title(title: str, disambiguation: dict, pos: int, context: RunContext) -> Optional[Character]:
    if pos in disambiguation:
        char = _recall(pos, disambiguation)
        if char is not None:
            logger.debug(f'Matched ambiguous reference using disambiguation, identified automatically as {repr(char)}.')

        return char

    else:
        print(colorama.Fore.LIGHTBLACK_EX + '\n'.join(context.prev))
        print(colorama.Style.BRIGHT + context.run)
        print(colorama.Fore.LIGHTBLACK_EX + '\n'.join(context.next))

        if yn_question(f'Ambiguous reference found for "{title}". Does this refer to a character?'):
            char = char_search(f"Who does this refer to?")
        else:
            char = None

        clear_screen()
        if char is not None:
            logger.debug(f'Matched ambiguous reference from "{title}" at {context.chapter}:{pos}, '
                         f'identified manually as {repr(char)}.')

        _save(pos, char, disambiguation)
        return char


def disambiguate_book(key: str):
    disambiguation_path = (disambiguation_dir / key).with_suffix('.yml')
    if not disambiguation_path.exists():
        disambiguation_path.parent.mkdir(parents=True, exist_ok=True)
        disambiguation_path.touch()

    with disambiguation_path.open(mode='r') as f:
        disambiguation = yaml.load(f, yaml.Loader)
        if disambiguation is None:
            disambiguation = {}

    tokenized_chapters = list(tokenize_chapters(key))
    for i, (chapter, tokens) in enumerate(tokenized_chapters):
        print(f"=== {key}: {chapter} ({i+1}/{len(tokenized_chapters)})===")
        if chapter not in disambiguation:
            disambiguation[chapter] = {}

        idx = 0
        while idx < len(tokens):
            found = []
            context = RunContext(chapter=chapter,
                                 prev=[s for s in (' '.join(tokens[max(0, idx - (i * RUN_SIZE)):
                                                                   max(0, idx - ((i - 1) * RUN_SIZE))]).strip()
                                                   for i in range(PREV_LINES, 0, -1)) if s],
                                 run=' '.join(tokens[idx:min(len(tokens), idx + RUN_SIZE)]),
                                 next=[s for s in (' '.join(tokens[min(len(tokens), idx + (i * RUN_SIZE)):
                                                                   min(len(tokens),
                                                                       idx + ((i + 1) * RUN_SIZE))]).strip()
                                                   for i in range(1, NEXT_LINES + 1)) if s]
                                 )

            i = 0
            tokens_remaining = len(tokens) - idx
            while i < min(RUN_SIZE, tokens_remaining):
                pos = idx + i

                this_token = tokens[pos]
                next_token = tokens[pos + 1] if pos + 1 < len(tokens) else ''
                third_token = tokens[pos + 2] if pos + 2 < len(tokens) else ''
                two_tokens = this_token + ' ' + next_token
                next_two_tokens = next_token + ' ' + third_token
                three_tokens = two_tokens + ' ' + third_token

                if three_tokens in lookup:
                    i += 3
                    if disambiguate_name(key, three_tokens, disambiguation[chapter], pos, context) is not None:
                        found.append(i)

                elif two_tokens in lookup:
                    i += 2
                    if disambiguate_name(key, two_tokens, disambiguation[chapter], pos, context) is not None:
                        found.append(i)

                elif this_token in constants.titles:
                    i += 1
                    if next_token not in lookup and next_two_tokens not in lookup:
                        if disambiguate_title(this_token, disambiguation[chapter], pos, context) is not None:
                            found.append(i)

                elif this_token in lookup:
                    i += 1
                    if disambiguate_name(key, this_token, disambiguation[chapter], pos, context) is not None:
                        found.append(i)

                else:
                    i += 1
                    continue

            # advance past first found character
            if len(found) >= 2:
                delta = found[0] + 1

            # advance until only character is at beginning of run (max threshold)
            elif len(found) == 1:
                delta = found[0] if found[0] > 0 else 1

            # skip run if no chars found
            else:
                delta = RUN_SIZE - 1

            idx += delta

        with disambiguation_path.open(mode='w') as f:
            yaml.dump(disambiguation, f, yaml.Dumper, default_flow_style=False, sort_keys=False)


def check_position(disambiguation, pos):
    if pos in disambiguation:
        char = _recall(pos, disambiguation)
        if char is not None:
            logger.debug(f'Matched ambiguous reference using disambiguation, identified automatically as {repr(char)}.')

        return char
    else:
        raise AmbiguousReferenceError(f"Reference at position {pos} not found in disambiguation. "
                                      f"Please run disambiguation again.")
