import operator
import requests
import json
import re

from pathlib import Path
from tqdm import tqdm


class Character:
    """representation of a character in the Cosmere."""
    def __init__(self, query_result: dict):
        """construct character from coppermind.net api query results."""
        self._discard = False
        self._pageid = int(query_result['pageid'])
        self._infobox_str = ""

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

    def _parse_infobox(self, query_result):
        """..."""

        # set defaults
        char_info = {}
        table_str = ""

        # define local utility functions
        def isolate_table(s: str):
            """isolate infobox from extraneous summary text in query results"""
            count = 0
            pos = 0
            for i, char in enumerate(s):
                if char == '{':
                    count += 1
                elif char == '}':
                    count -= 1
                if count == 0:
                    pos = i
                    break

            return s[:pos + 1] if pos else ""

        def sanitize_templates(s: str):
            """sanitize infobox key/value pairs"""
            brace, bracket = 0, 0
            sanitized = []
            for char in s:
                if char == '{':
                    brace += 1
                elif char == '[':
                    bracket += 1
                elif char == '}':
                    brace -= 1
                elif char == ']':
                    bracket -= 1

                # replace special chars with ':' if inside template entity
                if char in ('|', '=') and (brace > 0 or bracket > 0):
                    sanitized.append(':')
                else:
                    sanitized.append(char)

            return "".join(sanitized)

        # parse infobox
        if 'revisions' in query_result:
            if query_result['revisions']:
                content = query_result['revisions'][0]['content']

                # trim outermost template tags
                match = re.match(r'^{{((?:.\s?)*)}}$', isolate_table(content))
                if match:
                    # split string on field delimiter
                    table_str = sanitize_templates(match[1])
                    table = [e.strip() for e in table_str.split('|')]

                    # ignore non-character pages
                    if table.pop(0).lower() != 'character':
                        self._discard = True

                    # split into key/value pairs
                    for entry in table:
                        if entry:
                            m = re.match(r'^(\w+\b)(?:[\s=]+(.*))?$', entry)
                            if m:
                                # remove templating delimiters
                                k, v = m[1], re.sub(r'[\[{}\]]', '', m[2])

                                # ignore certain keywords
                                if k.lower() in ('image',):
                                    continue

                                # sanitize and process specific fields
                                # books
                                if k.lower() == 'books':
                                    v = [e.strip() for e in v.split(',')]
                                    v = [b.split(':')[-1] if any(s in b for s in ('(book)', '(series)')) else b
                                         for b in v]

                                # aliases
                                elif k.lower() == 'aliases':
                                    v = [e.strip() for e in v.split(',')]

                                # titles
                                elif k.lower() == 'titles':
                                    v = [e.strip() for e in v.split(',')]

                                # add to dict
                                char_info[k.lower()] = v

        # ignore non-cosmere characters
        cosmere_worlds = ('roshar', 'nalthis', 'scadrial', 'first of the sun', 'taldain', 'threnody', 'yolen', 'sel')
        if char_info.get('world', 'n/a').lower() not in cosmere_worlds:
            self._discard = True

        self._infobox_str = table_str
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
        num_pages = r.json()['query']['pages']['40']['categoryinfo']['pages']

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
            while True:
                req = payload.copy()
                req.update(continue_data)
                r = requests.get(wiki_api, params=req)
                response = r.json()
                if 'error' in response:
                    raise RuntimeError(response['error'])
                if 'warnings' in response:
                    print(response['warnings'])
                if 'query' in response:
                    yield response['query']['pages']
                if 'continue' not in response:
                    progressbar.update(len(response['query']['pages']))
                    break

                continue_data = response['continue']
                progressbar.update(len(response['query']['pages']))

    path = Path('data/characters.json')
    if path.exists():
        with path.open() as f:
            return json.load(f)
    else:
        print('downloading from coppermind.net...')
        results = [el for batch in _query() for el in batch]
        with path.open('w') as f:
            json.dump(results, f)
        return results


# get characters in the cosmere from coppermind.net
characters = sorted([Character(result) for result in coppermind_query()], key=operator.attrgetter('name'))
names = set(c.name for c in characters)


if __name__ == '__main__':

    # todo: names need more sanitizing
    print("people:", characters)
    print("all character names unique:", len(names) == len(list(c.name for c in characters)))
    print("all page ids unique:", len(set(e._pageid for e in characters)) == len(list(e._pageid for e in characters)))
    print("nations:", set(c.info.get('nation') for c in characters))
    print("worlds:", set(c.world for c in characters))
    print("books:", set(book for c in characters for book in c.books))
