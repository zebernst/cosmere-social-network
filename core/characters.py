import operator
import re
import typing
from collections import defaultdict

import mwparserfromhell as mwp
import requests
from mwparserfromhell.nodes import Wikilink, Template
from tqdm import tqdm

from core.constants import cleansed_fields, info_fields, nationalities, cosmere_planets
from utils.cache import cache
from utils.logs import create_logger
from utils.paths import coppermind_cache_path
from utils.wiki import extract_info


logger = create_logger('csn.core.characters')


class Character:
    """representation of a character in the Cosmere."""

    def __init__(self, query_result: dict):
        """construct character from coppermind.net api query results."""
        info = extract_info(query_result)

        self._keep = True
        self._pageid = info['pageid']
        self._infobox_template = ""

        self.name = info['title']
        self.info = self._parse_infobox(info['content'])
        self.common_name = self.info.pop('common_name', '')
        self.surname = self.info.pop('surname', '')
        self.aliases = self.info.pop('aliases', [])
        self.titles = self.info.pop('titles', [])
        self.world = self.info.pop('world', None)
        self.books = self.info.pop('books', None)
        self.abilities = self.info.pop('abilities', [])

        # discard unofficial character pages
        if 'User:' in self.name:
            self._keep = False

        # sanitize name
        if '(' in self.name:
            self.info['original_name'] = self.name
            self.name = re.sub(r"\s\([\w\s]+\)", '', self.name)

        if self._keep:
            logger.debug(f"Created  {self.name} ({self.world if self.world else 'Unknown'}).")
        else:
            logger.debug(f"Ignoring {self.name} ({self.world if self.world else 'Unknown'}).")

    def __eq__(self, other):
        """return self == value."""
        if isinstance(other, self.__class__):
            return self._pageid == other._pageid
        else:
            return False

    def __ne__(self, other):
        """return self != value."""
        return not self.__eq__(other)

    def __hash__(self):
        """return hash(self._pageid)."""
        return hash(self._pageid)

    def __repr__(self):
        """return repr(self)."""
        return f"<{self.name} (#{self._pageid}): {self.world}>"

    def __str__(self):
        """return str(self)."""
        return self.name

    @property
    def monikers(self) -> typing.Set[str]:
        """return a set of monikers that the character is known by."""
        return set([self.name, self.common_name, self.surname] + self.aliases + self.titles)

    @property
    def coppermind_url(self) -> str:
        """return the url of the character's page on coppermind.net"""
        return f"https://coppermind.net/wiki?curid={self._pageid}"

    def _parse_infobox(self, content: str) -> dict:
        """parse the wikitext infobox for character attributes"""

        # set defaults
        char_info = {}

        # define local utility functions
        def parse_markup(wikicode: mwp.wikicode.Wikicode):
            templates = wikicode.filter_templates()
            links = wikicode.filter_wikilinks()
            for t in templates:
                # remove references
                if 'ref' in t.name or 'wob' in t.name:
                    wikicode.remove(t)
            for l in links:
                # simplify links
                text = l.text if l.text else l.title
                wikicode.replace(l, Wikilink(text))

            # todo
            return wikicode

        def parse_names(wikicode: mwp.wikicode.Wikicode):
            wikicode = parse_markup(wikicode)
            for t in wikicode.filter(forcetype=Template):
                if len(t.params) == 1:
                    wikicode.replace(t, t.params[0])
                elif len(t.params) > 1:
                    if 'highprince' in t.params[0].lower():
                        wikicode.replace(t, "{0} of {1}".format(*t.params))
                    elif 'army' in t.params[0].lower():
                        wikicode.replace(t, "{1} {0}".format(*t.params))

            return wikicode.strip_code().split(',')

        def parse_abilities(wikicode: mwp.wikicode.Wikicode):
            wikicode = parse_markup(wikicode)
            abilities = []
            for wc in wikicode.filter(forcetype=(Template, Wikilink)):
                if isinstance(wc, Template):
                    if 'tag' in wc.name:
                        params = tuple(p.lower()
                                       for p in (p.name.strip_code()
                                                 if p.showkey is True
                                                 else p.value.strip_code()
                                                 for p in wc.params)
                                       if p != 'cat')

                        if len(params) == 1:
                            abilities.append(params[0])
                        elif len(params) > 1:
                            if any(params[0] == s for s in ('shard', 'vessel', 'splinter')):
                                abilities.extend((params[0], f"{params[0]} of {params[1]}"))
                            elif params[0] == 'squire':
                                abilities.append(f'squire ({params[1].split()[-1]})')
                            else:
                                print("unknown ability while parsing character: ", params)

                elif isinstance(wc, Wikilink):
                    abilities.append(wc.title.strip_code().lower())

            return abilities

        # parse infobox
        if content:
            # select outermost wiki template
            self._infobox_template = mwp.parse(content).filter_templates()
            if self._infobox_template:
                infobox = next((t for t in self._infobox_template if t.name.strip().lower() == 'character'), None)

                # ignore non-character pages
                if infobox is None:
                    self._keep = False
                    return char_info

                # ignore deleted characters (i.e. from early drafts)
                if any('deleted' in t.name.lower() for t in self._infobox_template):
                    self._keep = False
                    return char_info

                # split into key/value pairs
                for entry in infobox.params:
                    k, v = re.sub(r'[^a-z\-]', '', str(entry.name).lower()), entry.value

                    # normalize non-linking field names
                    if k.endswith('-raw'):
                        k = k[:-4]

                    # clean field names and correct typos
                    k = cleansed_fields.get(k, k)

                    if k not in info_fields:
                        continue

                    # sanitize and process specific fields
                    # books
                    if k == 'books':
                        v = [b.text.strip_code() if b.text else b.title.strip_code()
                             for b in v.nodes
                             if isinstance(b, mwp.wikicode.Wikilink)]

                    # normalize nation/nationality
                    elif k == 'nationality' or k == 'nation':
                        v = nationalities.get(v.strip_code().lower(), None)
                        k = 'nationality'

                    # titles and aliases and names
                    elif k == 'titles' or k == 'aliases' or k == 'name':
                        v = [name
                             for name in (name.strip() for name in parse_names(v))
                             if name]

                    # world
                    elif k == 'world' or k == 'universe':
                        v = v.strip_code()

                    # ignore unnamed minor characters
                    elif k == 'unnamed':
                        self._keep = False
                        return char_info

                    # parse wiki tags into human-readable text
                    else:
                        # v = parse_markup(v)
                        pass

                    # add to dict (null-guarded)
                    char_info[k] = v

                # sanitize abilities
                if 'abilities' in char_info:
                    char_info['abilities'] = parse_abilities(char_info['abilities'])

                # combine name and aliases
                if char_info.get('name'):
                    if char_info.get('aliases'):
                        char_info['aliases'].extend(char_info.pop('name'))
                    else:
                        char_info['aliases'] = char_info.pop('name')

                # isolate common name and surname
                names = self.name.split()
                if names[0] in ('King', 'Queen', 'Prince', 'Princess', 'Lord', 'Baron', 'Miss', 'Lady'):
                    char_info['common_name'] = ''
                    char_info['surname'] = names[-1]
                elif "'s" in self.name:
                    char_info['common_name'] = self.name
                    char_info['surname'] = ''
                else:
                    char_info['common_name'] = names[0]
                    char_info['surname'] = names[-1] if len(names) > 1 else ''


                # ignore non-cosmere characters
                if char_info.get('universe', '').lower() != 'cosmere':
                    self._keep = False

            # no valid template to parse
            else:
                self._keep = False

        return char_info


@cache(coppermind_cache_path)
def coppermind_query() -> typing.List[dict]:
    """load data from coppermind.net"""
    logger.info("Beginning query of coppermind.net.")

    def batched_query():
        """function to query coppermind.net api in batches for all character pages"""
        # query generator code based on https://www.mediawiki.org/wiki/API:Query#Continuing_queries
        wiki_api = "https://coppermind.net/w/api.php"

        # get total number of pages to fetch
        r = requests.get(wiki_api, params=dict(action='query', format='json',
                                               prop='categoryinfo', titles='Category:Characters'))
        num_pages = r.json().get('query', {}).get('pages', {}).get('40', {}).get('categoryinfo', {}).get('pages')

        # query server until finished
        payload = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "generator": "categorymembers",
            "rvprop": "content|timestamp",
            "rvsection": "0",
            "gcmtitle": "Category:Characters",
            "gcmprop": "ids|title",
            "gcmtype": "page",
            "gcmlimit": "50",
            "formatversion": 2
        }
        continue_data = {}
        with tqdm(total=num_pages, unit=' pages') as progress_bar:
            while continue_data is not None:
                req = payload.copy()
                req.update(continue_data)
                r = requests.get(wiki_api, params=req)
                response = r.json()
                num_results = len(response.get('query', {}).get('pages', []))
                logger.debug(f"Batch of {num_results} results received from coppermind.net.")
                if 'error' in response:
                    raise RuntimeError(response['error'])
                if 'warnings' in response:
                    print(response['warnings'])
                if 'query' in response:
                    yield response['query'].get('pages', [])

                continue_data = response.get('continue', None)
                progress_bar.update(num_results)

        logger.info("Finished query of coppermind.net.")

    return sorted((page
                   for batch in batched_query()
                   for page in batch),
                  key=operator.itemgetter('pageid'))

# todo: move modification to separate function in disambiguation.py


def _generate_characters() -> typing.Iterator[Character]:
    """generator wrapped over coppermind_query() in order to delay execution of http query"""
    logger.debug('Character generator initialized.')

    modify = {
        'Waxillium Ladrian': lambda c: c.aliases.append('Wax'),
        'Hoid': lambda c: c.aliases.remove('others'),
        'Gave Entrone': lambda c: re.sub(r".*", '', c.common_name)
    }

    for result in coppermind_query():
        char = Character(result)
        if char._keep:
            if char.name in modify:
                modify[char.name](char)
            yield char


# provide direct access to character generator
characters_ = _generate_characters()

if __name__ == '__main__':
    characters = list(characters_)
    pass
