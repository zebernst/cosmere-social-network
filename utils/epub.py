import operator
from pathlib import Path
import yaml

from utils.paths import book_dir, disambiguation_dir
from xml.etree import ElementTree
from pprint import pprint
from bs4 import BeautifulSoup
import re

from core.characters import characters_, Character


# easy access to book files
def book_files(name: str) -> Path:
    return book_dir / name / 'mobi8' / 'OEBPS'


if __name__ == '__main__':

    characters = list(characters_)

    book_content_regex = {
        'arcanum':                         None,
        'elantris':                        re.compile(r"^x_(chapter\d+|part\d+|(pro|epi)logue)"),
        'emperors-soul':                   re.compile(r"^x_book([3-9]|[1][0-8])"),
        'mistborn/era1/final-empire':      None,  # currently still has DRM
        'mistborn/era1/well-of-ascension': None,  # currently still has DRM
        'mistborn/era1/hero-of-ages':      re.compile(r"^x_(frontmatter03|part\d+(chapter\d+)?|backmatter01)"),
        'mistborn/era2/alloy-of-law':      re.compile(r"^x_(chapter\d+|(pro|epi)logue)"),
        'mistborn/era2/shadows-of-self':   re.compile(r"^x_(chapter\d+|(pro|epi)logue)"),
        'mistborn/era2/bands-of-mourning': re.compile(r"^x_(chapter\d+|(pro|epi)logue)"),
        'mistborn/secret-history':         re.compile(r"^x_book([3-9]|[1-2][0-9]|[3][0-4])"),
        'shadows-for-silence':             re.compile(r"^x_Shadows-for-Silence"),
        'sixth-of-the-dusk':               re.compile(r"^x_Sixth-of-the-Dusk"),
        'stormlight/way-of-kings':         re.compile(r"^x_([cp]\d+|pro|epi)"),
        'stormlight/words-of-radiance':    re.compile(r"^x_(chapter\d+|part\d+|inter\d+|(pro|epi)logue)"),
        'stormlight/edgedancer':           re.compile(r"^x_(chapter\d+|prologue)"),
        'stormlight/oathbringer':          re.compile(r"^x_(chapter\d+|part\d+|int(_part)?\d+|(pro|epi)logue)"),
        'warbreaker':                      re.compile(r"^x_(chapter\d+|(pro|epi)logue)")
    }

    key = 'mistborn/era2/bands-of-mourning'
    world = 'scadrial'
    book_dir = book_files(key)
    content_opf = ElementTree.parse(book_dir / 'content.opf').getroot()
    files = (book_dir / c.attrib['href']
             for c in content_opf.findall("opf:manifest/*[@media-type='application/xhtml+xml']",
                                          namespaces=dict(opf='http://www.idpf.org/2007/opf'))
             if book_content_regex.get(key).match(c.attrib['id']))

    sanitize = re.compile(r"[?!.,…'’“”‘]")

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

    char_ids = {c._pageid: c for c in characters}

    with (disambiguation_dir / key).with_suffix('.yml').open(mode='r') as f:
        disambiguation = yaml.load(f, yaml.Loader)
        if disambiguation is None:
            disambiguation = {}


    def clarify_REFACTORME(key, names: dict, line: str, world: str):
        this_world = [c for c in names[key] if c.world.lower() == world]
        if len(this_world) == 1:
            return this_world[0]

        print(f'Ambiguious reference found for `{key}`! Please choose the correct character that '
              f'appears in the following run:')
        print(line)
        for i2, name2 in enumerate(names[key]):
            print(f"  {i2 + 1}: {name2.name} ({name2.world}) -- {name2.info}")
        print("  o: The character is not listed.")
        print("  x: This is not a character.")
        response = input("> ")
        while not ((response.isdigit() and int(response) <= len(names[key]))
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
                return clarify_REFACTORME(response, names, line, world)
            else:
                return names[response]
        idx2 = int(response) - 1
        return names[key][idx2]

        # todo: implement `this is not a character` option
        # todo: implement `search for correct character`

    for cnt, chapter in enumerate(files):
        with chapter.open() as f:
            if chapter.name not in disambiguation:
                disambiguation[chapter.name] = {}

            soup = BeautifulSoup(f.read(), 'lxml')
            text = '\n'.join([e.text for e in soup.find_all('p', text=True)])
            text = re.sub(r"['’‘]s\b", '', text)
            text = re.sub(sanitize, '', text)
            tokens = [t for t in re.split(r'[\n\s—]+', text) if t]
            run_size = 25
            idx = 0
            while idx < len(tokens):
                local_tokens = tokens[idx:idx + run_size]
                run = ' '.join(local_tokens).strip()

                chars = []
                i = 0
                while i < len(local_tokens):
                    # for i, tok in enumerate(local_tokens):
                    name = local_tokens[i]
                    full_name = ' '.join(local_tokens[i:i+2])
                    char: Character = None

                    if full_name in monikers:
                        if isinstance(monikers[full_name], list):
                            if idx+i in disambiguation[chapter.name]:
                                char_id = disambiguation[chapter.name][idx+i]
                                char = char_ids[char_id] if char_id is not None else None
                            else:
                                char = clarify_REFACTORME(full_name, monikers, run, world)
                                disambiguation[chapter.name][idx+i] = char._pageid if char else None
                        else:
                            char = monikers[full_name]
                        i += 2

                    elif full_name not in monikers and name in ('Lady', 'Lord', 'Miss', 'Master'):
                        i += 1

                    elif name in monikers:
                        if isinstance(monikers[name], list):
                            if idx + i in disambiguation[chapter.name]:
                                char_id = disambiguation[chapter.name][idx+i]
                                char = char_ids[char_id] if char_id is not None else None
                            else:
                                char = clarify_REFACTORME(name, monikers, run, world)
                                disambiguation[chapter.name][idx+i] = char._pageid if char else None
                        else:
                            char = monikers[name]
                        i += 1

                    else:
                        i += 1

                    # todo: advance by two tokens if possible, else fall back to one

                    # todo: disambiguation stores word, resolved character, and position, checks if resolved
                    #       word exists within length of last run

                    if char is not None:
                        if char.world.lower() != world and 'worldhopping' not in char.abilities:
                            if idx+i not in disambiguation[chapter.name]:
                                print(f"Non-worldhopping character found! Please confirm presence "
                                      f"of {char.name} ({char.world}) in the following run:")
                                print(run)
                                disambiguation[chapter.name][idx+i] = input(">  character present? y/n: ").lower().startswith('y')
                            elif disambiguation[chapter.name][idx+i]:
                                chars.append((i, char))
                        else:
                            chars.append((i, char))

                # advance past first found character
                if len(chars) >= 2:
                    idx += chars[0][0]+1
                    print(f"{run:200s} // {chars}")

                # advance until only character is at beginning of run (max threshold)
                elif len(chars) == 1:
                    idx += chars[0][0] if chars[0][0] > 0 else 1
                    print(f"{run:200s} // {chars}")

                # skip run if no chars found
                else:
                    idx += run_size-1
                    print(f"{run:200s} // {chars}")

            with (disambiguation_dir / key).with_suffix('.yml').open(mode='w') as f:
                yaml.dump(disambiguation, f, yaml.Dumper)

    with (disambiguation_dir / key).with_suffix('.yml').open(mode='w') as f:
        yaml.dump(disambiguation, f, yaml.Dumper)

