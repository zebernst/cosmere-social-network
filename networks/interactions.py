import json
from itertools import combinations
from typing import Union

import networkx as nx
import yaml

from core.characters import characters, lookup
from core.config import InteractionNetworkConfig
from utils.constants import book_keys, titles
from utils.disambiguation import disambiguate_name, disambiguate_title, verify_presence
from utils.epub import tokenize_chapters
from utils.logs import create_logger
from utils.paths import disambiguation_dir, gml_dir, json_dir
from utils.simpletypes import CharacterOccurrence, RunContext


logger = create_logger('csn.networks.interactions')

RUN_SIZE = InteractionNetworkConfig.run_size
PREV_LINES = InteractionNetworkConfig.prev_cxt_lines
NEXT_LINES = InteractionNetworkConfig.next_cxt_lines

nodes = {c.id: c.properties for c in characters}
logger.debug('Created dictionary of nodes.')


def save_disambiguation(book: str, disambiguation: dict):
    with (disambiguation_dir / book).with_suffix('.yml').open(mode='w') as f:
        yaml.dump(disambiguation, f, yaml.Dumper, default_flow_style=False, sort_keys=False)


def combine_edges(G: nx.Graph, other: nx.Graph):
    for u, v, w in other.edges(data='weight'):
        if G.has_edge(u, v):
            G[u][v]['weight'] += w
        else:
            G.add_edge(u, v, weight=w)


def chapter_graph(book: str, chapter: str, tokens: list, disambiguation: dict):
    G = nx.Graph()
    G.add_nodes_from(nodes.items())

    if chapter not in disambiguation:
        disambiguation[chapter] = {}

    print(f"==== CHAPTER: {chapter} ====")

    idx = 0
    while idx < len(tokens):
        found = []
        context = RunContext(
            prev=[s for s in (' '.join(tokens[max(0, idx - (i * RUN_SIZE)):
                                              max(0, idx - ((i - 1) * RUN_SIZE))]).strip()
                              for i in range(PREV_LINES, 0, -1)) if s],
            run=' '.join(tokens[idx:min(len(tokens), idx + RUN_SIZE)]),
            next=[s for s in (' '.join(tokens[min(len(tokens), idx + (i * RUN_SIZE)):
                                              min(len(tokens), idx + ((i + 1) * RUN_SIZE))]).strip()
                              for i in range(1, NEXT_LINES + 1)) if s]
        )

        i = 0
        tokens_remaining = len(tokens) - idx
        while i < min(RUN_SIZE, tokens_remaining):
            char = None
            pos = idx + i

            this_token = tokens[pos]
            next_token = tokens[pos + 1] if pos + 1 < len(tokens) else ''
            third_token = tokens[pos + 2] if pos + 2 < len(tokens) else ''
            two_tokens = this_token + ' ' + next_token
            next_two_tokens = next_token + ' ' + third_token
            three_tokens = two_tokens + ' ' + third_token

            if three_tokens in lookup:
                matches = lookup[three_tokens]
                if len(matches) > 1:
                    char = disambiguate_name(book, three_tokens, disambiguation[chapter], pos, context)
                else:
                    char = matches[0] if verify_presence(book, matches[0], three_tokens) else None

                i += 3

            elif two_tokens in lookup:
                matches = lookup[two_tokens]
                if len(matches) > 1:
                    char = disambiguate_name(book, two_tokens, disambiguation[chapter], pos, context)
                else:
                    char = matches[0] if verify_presence(book, matches[0], two_tokens) else None

                i += 2

            elif this_token in titles:
                if next_token not in lookup and next_two_tokens not in lookup:
                    char = disambiguate_title(this_token, disambiguation[chapter], pos, context)
                i += 1

            elif this_token in lookup:
                matches = lookup[this_token]
                if len(matches) > 1:
                    char = disambiguate_name(book, this_token, disambiguation[chapter], pos, context)
                else:
                    char = matches[0] if verify_presence(book, matches[0], this_token) else None

                i += 1

            else:
                i += 1
                continue

            if char is not None:
                found.append(CharacterOccurrence(i, char))

        # advance past first found character
        if len(found) >= 2:
            idx += found[0].pos + 1

        # advance until only character is at beginning of run (max threshold)
        elif len(found) == 1:
            idx += found[0].pos if found[0].pos > 0 else 1

        # skip run if no chars found
        else:
            idx += RUN_SIZE - 1

        chars = set(co.char for co in found)
        if len(chars) > 1:
            for u, v in combinations(chars, r=2):
                if G.has_edge(u.id, v.id):
                    G[u.id][v.id]['weight'] += 1
                else:
                    G.add_edge(u.id, v.id, weight=1)

                logger.debug(f'Added edge ({u.name} #{u.id}, {v.name} #{v.id}) from run "{context.run}"')

    G.remove_nodes_from(list(nx.isolates(G)))
    return G


def book_graph(book: str, min_weight: int = InteractionNetworkConfig.default_min_weight):
    G = nx.Graph()
    G.add_nodes_from(nodes.items())

    with (disambiguation_dir / book).with_suffix('.yml').open(mode='r') as f:
        disambiguation = yaml.load(f, yaml.Loader)
        if disambiguation is None:
            disambiguation = {}

    for chapter, tokens in tokenize_chapters(book):
        sG = chapter_graph(book, chapter, tokens, disambiguation)
        combine_edges(G, sG)
        save_disambiguation(book, disambiguation)

    G.remove_edges_from([(u, v) for (u, v, w) in G.edges(data='weight')
                         if w < min_weight
                         and u != 13  # Hoid
                         and v != 13])
    G.remove_nodes_from(list(nx.isolates(G)))
    return G


def series_graph(series: str):
    G = nx.Graph()
    G.add_nodes_from(nodes.items())

    for book in (b for b in book_keys if b.startswith(series)):
        sG = book_graph(book, min_weight=0)
        combine_edges(G, sG)

    return G


def book_progression(book: str):
    with (disambiguation_dir / book).with_suffix('.yml').open(mode='r') as f:
        disambiguation = yaml.load(f, yaml.Loader)
        if disambiguation is None:
            disambiguation = {}

    chapters = []
    for chapter, tokens in tokenize_chapters(book):
        chapters.append(chapter_graph(book, chapter, tokens, disambiguation))
        save_disambiguation(book, disambiguation)

    return chapters


def series_progression(series: str):
    chapters = []
    for book in (b for b in book_keys if b.startswith(series)):
        chapters.extend(book_progression(book))

    return chapters


def save_network_gml(key: str, G: Union[nx.Graph, nx.OrderedGraph]):
    filename = gml_dir / 'interactions' / f'{key}.gml'
    filename.parent.mkdir(parents=True, exist_ok=True)

    nx.write_gml(G, str(filename), stringizer=lambda p: str(p) if p else "null")
    logger.info(f"GML  graph data for {key} characters written to {filename}")


def save_network_json(key: str, G: Union[nx.Graph, nx.OrderedGraph]):
    filename = json_dir / 'interactions' / f'{key}.json'
    filename.parent.mkdir(parents=True, exist_ok=True)

    with filename.open(mode='w') as f:
        json.dump(nx.node_link_data(G), f)
    logger.info(f"JSON graph data for {key} characters written to {filename}")


if __name__ == '__main__':

    for key in book_keys:
        if key not in ('stormlight/way-of-kings',):
            continue

        graph = book_graph(key)
        save_network_gml(key, graph)
        save_network_json(key, graph)
        print('done!')

