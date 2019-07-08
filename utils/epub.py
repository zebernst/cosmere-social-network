from pathlib import Path

from utils.paths import book_dir
from xml.etree import ElementTree
from pprint import pprint
from bs4 import BeautifulSoup
import re

from core.characters import characters_


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

    ns = {'opf': 'http://www.idpf.org/2007/opf'}

    key = 'mistborn/era2/bands-of-mourning'
    world = 'scadrial'
    book_dir = book_files(key)
    root = ElementTree.parse(book_dir / 'content.opf').getroot()
    files = (book_dir / c.attrib['href']
             for c in root.findall("opf:manifest/*[@media-type='application/xhtml+xml']", ns)
             if book_content_regex.get(key).match(c.attrib['id']))

    sanitize = re.compile(r"[?!.,…'’“”]")
    monikers = {re.sub(sanitize, '', name): c
                for c in characters
                for name in c.monikers
                if name is not None}
    # and (c.world == world or c.info.get(''))}

    for m in monikers:
        if ' ' in m.lower() and monikers[m].common_name:
            print(m, '--', monikers[m].common_name)

    for cnt, chapter in enumerate(files):
        with chapter.open() as f:
            if cnt == 2:
                print(chapter)
                soup = BeautifulSoup(f.read(), 'lxml')
                text = '\n'.join([e.text for e in soup.find_all('p', text=True)])
                tokens = re.split(r'[\n\s—]+', re.sub(sanitize, '', text))
                for i in range(len(tokens) - 15 + 1):
                    run = ' '.join(tokens[i:i + 15])
                    chars = set((tok, monikers[tok]) for tok in run.split() if tok in monikers)
                    if len(chars) > 1:
                        print(i, chars)
                break

            # print(len(f.readlines()), 'lines long')

    # pprint(root)
