import requests
import json
import re

from pathlib import Path
from tqdm import tqdm


def query():
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


def load_query_results():
    """load and cache data from coppermind.net"""
    path = Path('data/characters.json')
    if path.exists():
        with path.open() as f:
            return json.load(f)
    else:
        print('downloading from coppermind.net...')
        results = [el for batch in query() for el in batch]
        with path.open('w') as f:
            json.dump(results, f)
        return results


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

    return s[:pos+1] if pos else ""


def sanitize_attrs(s: str):
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


def process_data():
    """get characters in the cosmere from coppermind.net"""
    chars = []
    for result in load_query_results():

        # set defaults
        char_info = {}
        table_str = ""

        # parse infobox
        if 'revisions' in result:
            if result['revisions']:
                content = result['revisions'][0]['content']

                # get infobox template content
                s = isolate_table(content)

                # trim outermost template tags
                match = re.match(r'^{{((?:.\s?)*)}}$', isolate_table(content))
                if match:
                    # split string on field delimiter
                    table_str = sanitize_attrs(match[1])
                    table = [e.strip() for e in table_str.split('|')]

                    # ignore non-character pages
                    if table.pop(0).lower() != 'character':
                        continue

                    # split into key/value pairs
                    for entry in table:
                        if entry:
                            m = re.match(r'^(\w+\b)(?:[\s=]+(.*))?$', entry)
                            if m:
                                k, v = m[1], re.sub(r'[\[{}\]]', '', m[2])

                                # sanitize and process specific fields
                                if k.lower() == 'books':
                                    v = [e.strip() for e in v.split(',')]
                                    v = [b.split(':')[-1] if any(s in b for s in ('(book)', '(series)')) else b for b in
                                         v]

                                char_info[k] = v

        # ignore non-cosmere characters
        cosmere_worlds = ('roshar', 'nalthis', 'scadrial', 'first of the sun', 'taldain', 'threnody', 'yolen', 'sel')
        if char_info.get('world', 'n/a').lower() not in cosmere_worlds:
            continue

        # add to character list
        chars.append({
            'name': result['title'],
            'wiki_id': result['pageid'],
            'properties': char_info,
            'debug_str': table_str
        })

    return chars


characters = process_data()
names = set(c.get('name') for c in characters)


if __name__ == '__main__':

    people = characters

    # todo: names need more sanitizing
    print("people:", names)

    print("nations:", set(c['properties'].get('nation') for c in people))
    print("worlds:", set(c['properties'].get('world') for c in people))
    print("books:", set(b for c in people for b in c['properties'].get('books')))
