import pickle

import requests
import json
from enum import Enum
import re

from pathlib import Path
from itertools import groupby

wiki_api = "https://coppermind.net/w/api.php"


def continuable_query(params: dict):
    last_continue = {}

    while True:
        req = params.copy()
        req.update(last_continue)
        r = requests.get(wiki_api, params=req)
        response = r.json()
        if 'error' in response:
            raise RuntimeError(response['error'])
        if 'warnings' in response:
            print(response['warnings'])
        if 'query' in response:
            yield response['query']['pages']
        if 'continue' not in response:
            break
        last_continue = response['continue']


def load_query_results():
    path = Path('data/characters.json')
    if path.exists():
        with path.open() as f:
            return json.load(f)
    else:
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
        results = [e for l in continuable_query(payload) for e in l]
        with path.open('w') as f:
            json.dump(results, f)
        return results


def isolate_table(s: str):
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


def replace_delimiter(s: str):
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

        if char in ('|', '=') and (brace > 0 or bracket > 0):
            sanitized.append(':')
        else:
            sanitized.append(char)

    return "".join(sanitized)


if __name__ == '__main__':
    characters = []
    query_results = load_query_results()
    for i, result in enumerate(query_results):

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
                    table_str = replace_delimiter(match[1])
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
                                    v = [b.split(':')[-1] if any(s in b for s in ('(book)', '(series)')) else b for b in v]

                                char_info[k] = v

        # ignore non-cosmere characters
        cosmere_worlds = ('roshar', 'nalthis', 'scadrial', 'first of the sun', 'taldain', 'threnody', 'yolen', 'sel')
        if char_info.get('world', 'n/a').lower() not in cosmere_worlds:
            continue

        # add to character list
        characters.append({
            'name': result['title'],
            'wiki_id': result['pageid'],
            'properties': char_info,
            'debug_str': table_str
        })

    print("nations:", set(c['properties'].get('nation') for c in characters))
    print("worlds:", set(c['properties'].get('world') for c in characters))
    print("books:", set(b for c in characters for b in c['properties'].get('books')))

    buckets = []
    for k, grp in groupby(sorted(characters, key=lambda e: e['properties'].get('world')), key=lambda e: e['properties'].get('world')):
        buckets.append((k, list(grp)))
    print('buckets')
