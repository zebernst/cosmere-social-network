import json
from itertools import combinations
from typing import Union

import networkx as nx
import yaml

from core.characters import Character, characters, monikers
from core.constants import book_keys, titles
from core.disambiguation import disambiguate_name, disambiguate_title, verify_presence
from utils.epub import chapters
from utils.logs import create_logger
from utils.paths import disambiguation_dir, gml_dir, json_dir
from utils.types import RunContext


logger = create_logger('csn.networks.interactions')


def create_graph(book: str, min_weight: int = 3):
    G = nx.Graph()

    nodes = {c.id: dict(name=c.name, world=c.world)
             for c in characters}
    G.add_nodes_from(nodes.items())

    with (disambiguation_dir / book).with_suffix('.yml').open(mode='r') as f:
        disambiguation = yaml.load(f, yaml.Loader)
        if disambiguation is None:
            disambiguation = {}

    for chapter, tokens in chapters(book):
        run_size = 25
        idx = 0

        if chapter not in disambiguation:
            disambiguation[chapter] = {}

        while idx < len(tokens):
            local_tokens = tokens[idx:idx + run_size]
            context = RunContext(prev=[' '.join(tokens[idx - (i*run_size):idx - ((i-1)*run_size)]).strip()
                                       for i in range(4, 0, -1)],
                                 run=' '.join(tokens[idx:idx + run_size]),
                                 next=[' '.join(tokens[idx + (i*run_size):idx + ((i+1)*run_size)]).strip()
                                       for i in range(1, 3)])

            found = []
            i = 0
            while i < len(local_tokens):
                char: Character = None
                pos = idx + i

                this_token = local_tokens[i]
                next_token = local_tokens[i + 1] if i + 1 < len(local_tokens) else ''
                third_token = local_tokens[i + 2] if i + 2 < len(local_tokens) else ''
                two_tokens = this_token + ' ' + next_token
                next_two_tokens = next_token + ' ' + third_token
                three_tokens = two_tokens + ' ' + third_token

                if three_tokens in monikers:
                    if isinstance(monikers[three_tokens], list):
                        char = disambiguate_name(book, three_tokens, disambiguation[chapter], pos, context)
                    else:
                        char = monikers[three_tokens] if verify_presence(book, monikers[three_tokens],
                                                                         three_tokens) else None

                    i += 3

                elif two_tokens in monikers:
                    if isinstance(monikers[two_tokens], list):
                        char = disambiguate_name(book, two_tokens, disambiguation[chapter], pos, context)
                    else:
                        char = monikers[two_tokens] if verify_presence(book, monikers[two_tokens], two_tokens) else None

                    i += 2

                elif this_token in titles:
                    if next_token not in monikers and next_two_tokens not in monikers:
                        char = disambiguate_title(this_token, disambiguation[chapter], pos, context)
                    i += 1

                elif this_token in monikers:
                    if isinstance(monikers[this_token], list):
                        char = disambiguate_name(book, this_token, disambiguation[chapter], pos, context)
                    else:
                        char = monikers[this_token] if verify_presence(book, monikers[this_token], this_token) else None

                    i += 1

                else:
                    i += 1
                    continue

                if char is not None:
                    found.append((i, char))

            # advance past first found character
            if len(found) >= 2:
                idx += found[0][0] + 1

            # advance until only character is at beginning of run (max threshold)
            elif len(found) == 1:
                idx += found[0][0] if found[0][0] > 0 else 1

            # skip run if no chars found
            else:
                idx += run_size - 1

            chars = set(c for i, c in found)
            if len(chars) > 1:
                for u, v in combinations(chars, r=2):
                    if G.has_edge(u.id, v.id):
                        G[u.id][v.id]['weight'] += 1
                    else:
                        G.add_edge(u.id, v.id, weight=1)

                    logger.debug(f'Added edge ({u.name} #{u.id}, {v.name} #{v.id}) from run "{context.run}"')

        with (disambiguation_dir / book).with_suffix('.yml').open(mode='w') as f:
            yaml.dump(disambiguation, f, yaml.Dumper, default_flow_style=False, sort_keys=False)

    G.remove_edges_from([(u, v) for (u, v, w) in G.edges(data='weight')
                         if w < min_weight
                         and u != 13  # Hoid
                         and v != 13])
    G.remove_nodes_from(list(nx.isolates(G)))
    return G


def save_network_gml(key: str, G: Union[nx.Graph, nx.OrderedGraph]):
    filename = gml_dir / 'interactions' / f'{key}.gml'
    filename.parent.mkdir(parents=True, exist_ok=True)

    nx.write_gml(G, str(filename))
    logger.info(f"GML  graph data for {key} characters written to {filename}")


def save_network_json(key: str, G: Union[nx.Graph, nx.OrderedGraph]):
    filename = json_dir / 'interactions' / f'{key}.json'
    filename.parent.mkdir(parents=True, exist_ok=True)

    with filename.open(mode='w') as f:
        json.dump(nx.node_link_data(G), f)
    logger.info(f"JSON graph data for {key} characters written to {filename}")


if __name__ == '__main__':

    for key in book_keys:
        if key != 'elantris':
            continue

        G = create_graph(key)
        save_network_gml(key, G)
        save_network_json(key, G)
        print('done!')

