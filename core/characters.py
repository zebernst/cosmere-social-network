import operator
import requests
import re

import mwparserfromhell as mwp
from tqdm import tqdm

from core.constants import cosmere_planets, nationalities, info_fields
from utils.caching import cache
from utils.logging import create_logger
from utils.paths import coppermind_cache_path


logger = create_logger('csn.core.characters')


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

        # discard duplicate character pages
        if 'User:' in self.name:
            self._discard = True

        logger.debug(f"Character {self.name} from {self.world} created.")
        if self._discard:
            logger.debug(f"{self.name} marked as discard.")

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
        def parse_markup(wikicode: mwp.wikicode.Wikicode):
            templates = wikicode.filter_templates()
            links = wikicode.filter_wikilinks()
            for t in templates:
                # remove references
                if 'ref' in t.name:
                    wikicode.remove(t)
                elif 'tag' in t.name:
                    if len(t.params) == 1:
                        wikicode.replace(t, t.params[0])
                    elif len(t.params) > 1:
                        if 'highprince' in t.params[0].lower():
                            wikicode.replace(t, "{0} of {1}".format(*t.params))
                        elif 'army' in t.params[0].lower():
                            wikicode.replace(t, "{1} {0}".format(*t.params))
            for l in links:
                text = l.text if l.text else l.title
                wikicode.replace(l, text)
            # todo
            return wikicode.strip_code()

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

                    # ignore deleted characters (i.e. from early drafts)
                    if any('deleted' in t.name.lower() for t in self._infobox_template):
                        self._discard = True

                    # split into key/value pairs
                    for entry in infobox.params:

                        k, v = re.sub(r'[^A-Za-z\-]', '', str(entry.name)).lower(), entry.value

                        # ignore certain keywords
                        cleanse_field = {
                            'residnece': 'residence',
                            'residence-raw': 'residence',
                            'residency': 'residence',
                            'nantion': 'nation',
                            'group': 'groups',
                            'nickname': 'aliases',
                            'powers': 'abilities',
                            'title': 'titles',
                            'occupation': 'profession'
                        }
                        k = cleanse_field.get(k, k)

                        if k not in info_fields:
                            continue

                        # sanitize and process specific fields
                        # books
                        if k == 'books':
                            v = [b.text.strip_code() if b.text else b.title.strip_code() for b in v.nodes
                                 if isinstance(b, mwp.wikicode.Wikilink)]

                        # normalize nation/nationality
                        elif k == 'nationality' or k == 'nation':
                            v = nationalities.get(v.strip_code().lower(), None)
                            k = 'nationality'

                        # titles and aliases and names
                        elif k == 'titles' or k == 'aliases' or k == 'name':
                            v = [e.strip() for e in parse_markup(v).split(',') if e.strip()]
                            pass

                        # world
                        elif k == 'world':
                            v = v.strip_code()

                        # ignore unnamed minor characters
                        elif k == 'unnamed':
                            self._discard = True

                        # parse wiki tags into human-readable text
                        else:
                            # v = parse_markup(v)
                            pass

                        # add to dict (null-guarded)
                        char_info[k] = v

                    # combine name and aliases
                    if char_info.get('name'):
                        if char_info.get('aliases'):
                            char_info['aliases'].extend(char_info.pop('name'))
                        else:
                            char_info['aliases'] = char_info.pop('name')

                    # ignore non-cosmere characters
                    if char_info.get('world', '').lower() not in cosmere_planets:
                        self._discard = True

                # no valid template to parse
                else:
                    self._discard = True

        return char_info


@cache(coppermind_cache_path)
def coppermind_query():
    """load data from coppermind.net"""
    logger.debug("Beginning query of coppermind.net.")

    def _query():
        """generator to query coppermind.net api for all characters"""
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
                logger.debug("Batch of 50 results received from coppermind.net.")
                if 'error' in response:
                    raise RuntimeError(response['error'])
                if 'warnings' in response:
                    print(response['warnings'])
                if 'query' in response:
                    yield response['query'].get('pages', [])

                continue_data = response.get('continue', None)
                progressbar.update(len(response['query']['pages']))

        logger.debug("Finished query of coppermind.net.")

    return sorted((page for batch in _query() for page in batch), key=operator.itemgetter('pageid'))


# construct, filter, and return character objects from coppermind.net data
characters_ = (c for c in (Character(result) for result in coppermind_query()) if not c._discard)
logger.debug('Character generator initialized.')

if __name__ == '__main__':
    print("names to sanitize:", [c for c in characters_ if '(' in c.name])

