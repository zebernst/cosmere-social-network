import operator
from pathlib import Path
import yaml

from utils.paths import book_dir
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

    # and (c.world == world or c.info.get(''))}

    # for m in monikers:
    #     if ' ' in m.lower() and monikers[m].common_name:
    #         print(m, '--', monikers[m].common_name)

    disambiguation = {}
    if key not in disambiguation:
        disambiguation[key] = {}

    for cnt, chapter in enumerate(files):
        with chapter.open() as f:
            if cnt == 3:
                print(chapter)
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
                    # chars = sorted(((i, monikers[tok])
                    #                 for i, tok in enumerate(local_tokens)
                    #                 if tok in monikers),
                    #                key=operator.itemgetter(0))

                    def clarify_REFACTORME(keyword, names: list, line: str, world: str):
                        this_world = [c for c in names if c.world.lower() == world]
                        if len(this_world) == 1:
                            return this_world[0]

                        print(f'Ambiguious reference found for `{keyword}`! Which character listed below '
                              f'is found in the following run?:')
                        print(line)
                        for i2, name2 in enumerate(names):
                            print(f"  {i2+1}: {name2.name} ({name2.world}) -- {name2.info}")
                        print("  0: None of these are correct.")
                        response = input("> ")
                        while not response.isdigit() or int(response) > len(names):
                            response = input("> ")
                        idx2 = int(response) - 1
                        if idx2 < 0:
                            return None
                        else:
                            return names[idx2]

                        # todo: implement `this is not a character` option

                    chars = []
                    for i, tok in enumerate(local_tokens):
                        name = tok
                        char: Character = None
                        if tok in ('Lord', 'Miss') and i+1 < len(local_tokens):  # ...
                            titled_name = ' '.join(local_tokens[i:i+1])
                            if titled_name in monikers:
                                if isinstance(monikers[titled_name], list):
                                    char = clarify_REFACTORME(titled_name, monikers[titled_name], run, world)
                                elif isinstance(monikers[titled_name], Character):
                                    char = monikers[titled_name]

                        if char is None:
                            if name in monikers:
                                if isinstance(monikers[name], list):
                                    char = clarify_REFACTORME(name, monikers[name], run, world)
                                elif isinstance(monikers[name], Character):
                                    char = monikers[name]

                        # todo: disambiguation stores word, resolved character, and position, checks if resolved
                        #       word exists within length of last run

                        if char:
                            if char.world.lower() != world and 'worldhopping' not in char.abilities:
                                if char.name not in disambiguation[key]:
                                    print(f"Non-worldhopping character found! Please confirm presence "
                                          f"of {char.name} ({char.world}) in the following run:")
                                    print(run)
                                    disambiguation[key][char.name] = {
                                        'present': input(">  character present? y/n: ").lower().startswith('y'),
                                        'loc': idx + i
                                    }
                                elif disambiguation[key][char.name]['present']:
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
                break

    # pprint(root)
