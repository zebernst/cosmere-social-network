import re
from xml.etree import ElementTree

from bs4 import BeautifulSoup

from utils.logs import create_logger
from utils.paths import book_dir


logger = create_logger('csn.utils.epub')

content_map = {
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


def chapters(key: str):
    chapter_dir = book_dir / key / 'mobi8' / 'OEBPS'

    content_opf = ElementTree.parse(chapter_dir / 'content.opf').getroot()
    files = [(c.attrib['id'], chapter_dir / c.attrib['href'])
             for c in content_opf.findall("opf:manifest/*[@media-type='application/xhtml+xml']",
                                          namespaces=dict(opf='http://www.idpf.org/2007/opf'))
             if content_map.get(key).match(c.attrib['id'])]

    logger.debug(f"Identified {len(files)} chapters to parse from {key}.")

    sanitize = re.compile(r"[?!.,…'’“”‘]")

    for chapter, path in files:
        with path.open() as f:
            soup = BeautifulSoup(f.read(), 'lxml')
            text = '\n'.join([e.text for e in soup.find_all('p', text=True)])
            text = re.sub(r"['’‘]s\b", '', text)
            text = re.sub(sanitize, '', text)
            tokens = [t for t in re.split(r'[\n\s—]+', text) if t]
            yield chapter, tokens