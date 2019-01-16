import operator
import requests
import json
import re

import mwparserfromhell as mwp

from pathlib import Path
from pprint import pprint
from tqdm import tqdm


class Character:
    """representation of a character in the Cosmere."""
    def __init__(self, query_result: dict):
        """construct character from coppermind.net api query results."""
        self._discard = False
        self._pageid = int(query_result['pageid'])
        self._infobox_template = ""

        self.name = query_result['title']
        self.info = self._parse_infobox(query_result)
        self.aliases = self.info.pop('aliases', [])
        self.titles = self.info.pop('titles', [])
        self.world = self.info.pop('world', None)
        self.books = self.info.pop('books', None)

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
        return f"<{self.name} ({self._pageid}): {self.world}>"

    def __str__(self):
        """return str(self)."""
        return f"{self.name}"

    @property
    def monikers(self):
        """return a set of monikers that the character is known by."""
        return set(n for n in [self.name] + self.aliases + self.titles)

    @property
    def coppermind_url(self):
        """return the url of the character's page on coppermind.net"""
        return f"https://coppermind.net/wiki?curid={self._pageid}"

    def _parse_infobox(self, query_result):
        """..."""

        # set defaults
        char_info = {}

        # define local utility functions
        def parse_markup(template):
            # todo
            pass

        # parse infobox
        if 'revisions' in query_result:
            if query_result['revisions']:
                content = query_result['revisions'][0]['content']

                # select outermost wiki template
                self._infobox_template = mwp.parse(content).filter_templates()
                if self._infobox_template:
                    infobox = self._infobox_template[0]

                    # ignore non-character pages
                    if infobox.name.strip().lower() != 'character':
                        self._discard = True

                    # split into key/value pairs
                    for entry in infobox.params:

                        k, v = re.sub(r'[^A-Za-z\-]', '', str(entry.name)).lower(), entry.value

                        # ignore certain keywords
                        # todo: normalize fields with a dictionary
                        fields = ('name', 'aliases', 'books', 'titles', 'title', 'world', 'abilities', 'powers'
                                  'family', 'parents', 'siblings', 'relatives', 'spouse', 'children', 'bonded', 'descendants', 'ancestors'
                                  'residence', 'residence-raw', 'residnece', 'groups', 'group', 'nation', 'nantion', 'profession', 'ethnicity',
                                  'species', 'occupation', 'born', 'died', 'unnamed')

                        if not k or k in ('image', ):
                            continue

                        # sanitize and process specific fields
                        # books
                        if k == 'books':
                            v = [b.text.strip_code() if b.text else b.title.strip_code() for b in v.nodes
                                 if isinstance(b, mwp.wikicode.Wikilink)]

                        # aliases
                        elif k == 'aliases':
                            # v = [e.strip() for e in v.split(',')]
                            pass

                        # titles
                        elif k == 'titles':
                            # v = [e.strip() for e in v.split(',')]
                            pass

                        # world
                        elif k == 'world':
                            v = v.strip_code()

                            # ignore non-cosmere characters
                            if v.lower() not in ('roshar', 'nalthis', 'scadrial', 'first of the sun',
                                                 'taldain', 'threnody', 'yolen', 'sel'):
                                self._discard = True

                        # add to dict
                        char_info[k] = v

                # no valid template to parse
                else:
                    self._discard = True

        return char_info


def coppermind_query():
    """load and cache data from coppermind.net"""

    def _query():
        """query coppermind.net api for all characters"""
        # base code taken from https://www.mediawiki.org/wiki/API:Query#Continuing_queries
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
            "rvprop": "content",
            "rvsection": "0",
            "gcmtitle": "Category:Characters",
            "gcmprop": "ids|title",
            "gcmtype": "page",
            "gcmlimit": "50",
            "formatversion": 2
        }
        continue_data = {}
        with tqdm(total=num_pages, unit=' pages') as progressbar:
            while continue_data is not None:
                req = payload.copy()
                req.update(continue_data)
                r = requests.get(wiki_api, params=req)
                response = r.json()
                if 'error' in response:
                    raise RuntimeError(response['error'])
                if 'warnings' in response:
                    print(response['warnings'])
                if 'query' in response:
                    yield response['query'].get('pages', [])

                continue_data = response.get('continue', None)
                progressbar.update(len(response['query']['pages']))

    path = Path('data/characters.json')
    if path.is_file():
        with path.open() as f:
            return json.load(f)
    else:
        print('downloading from coppermind.net...')
        results = [page for batch in _query() for page in batch]
        with path.open('w') as f:
            json.dump(results, f)
        return results


# get characters in the cosmere from coppermind.net
characters = sorted([c for c in (Character(result) for result in coppermind_query()) if not c._discard],
                    key=operator.attrgetter('name'))
names = set(c.name for c in characters)


if __name__ == '__main__':

    # todo: names need more sanitizing
    print("people:", characters)
    pprint(set(k.strip() for c in characters for k in c.info.keys()))
    print("all character names unique:", len(names) == len(list(c.name for c in characters)))
    print("all page ids unique:", len(set(e._pageid for e in characters)) == len(list(e._pageid for e in characters)))
    print("nations:", set(c.info.get('nation') for c in characters))
    print("worlds:", set(c.world for c in characters))
    print("books:", set(book for c in characters for book in c.books))

    # pprint(set((k, v) for c in characters for k, v in c.info.items() if any(x in v for x in '[{<>}]')))
