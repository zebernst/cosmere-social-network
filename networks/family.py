import json
from itertools import groupby

import networkx as nx
import mwparserfromhell as mwp

from core.characters import characters_
from core.constants import network_scopes
from utils.paths import gml_dir, json_dir
from utils.logging import create_logger


logger = create_logger('csn.networks.family')


def create_graph():
    # define relevant fields for analysis
    fields = ('parents', 'siblings', 'spouse', 'children', 'bonded')  # currently: nuclear family only
    unused_fields = ('descendants', 'ancestors', 'family', 'relatives')

    # create graph
    G = nx.Graph()

    # resolve generator
    characters = tuple(characters_)

    # restructure character list into efficient data structures to reduce complexity
    monikers = {name: c for c in characters for name in c.monikers}

    # filter on characters who have family info and add nodes to graph
    nodes = {c.name: dict(world=c.world) for c in characters if any(x in c.info for x in fields)}
    G.add_nodes_from(nodes.items())
    logger.debug("Added character nodes to graph.")

    # add edges between relevant nodes
    for c in characters:
        # ignore characters with no family info
        if c.name not in nodes:
            continue

        # loop through character's family connections
        for cxns in (c.info[k] for k in fields if k in c.info):
            for link in mwp.parse(cxns).filter_wikilinks():
                # sanitize
                relation = link.title.strip_code()
                if '_' in relation:
                    relation = relation.replace('_', ' ')
                if "'s " in relation:
                    continue

                # get potential full name
                forename = relation.split(' ')[0]
                surname = c.name.split(' ')[-1]

                target = None

                # if direct match found, add edge to graph
                if relation in nodes:
                    target = relation
                    logger.debug(f'Identified exact target of edge ({c.name}, {relation}).')

                # check if characters share a surname
                elif f"{forename} {surname}" in nodes:
                    target = f"{forename} {surname}"
                    logger.debug(f'Identified likely target of edge ({c.name}, {relation}) '
                                 f'to be {forename} {surname} via surname.')

                # check if connection matches any character aliases
                elif relation in monikers:
                    target = monikers[relation].name
                    logger.debug(f'Identified likely target of edge ({c.name}, {relation}) '
                                 f'to be {monikers[relation].name} via alias.')

                # last resort: loop through all characters and match substrings
                else:
                    found = False
                    for name, char in monikers.items():
                        if relation in name:
                            target = char.name
                            found = True
                            logger.debug(f'Could not confirm target of edge ({c.name}, {relation}), assuming {name}.')
                            break
                    if not found:
                        logger.info(f'Could not identify target of edge ({c.name}, {relation}).')

                # add edge if target is valid
                if target and target in nodes:
                    G.add_edge(c.name, target)

    return G


def filter_graph(G: nx.Graph, min_component_size=1):
    # create copy of input graph
    G = G.copy()

    # remove discrete components with less than 3 nodes.
    small_components = [c for c in nx.connected_components(G) if len(c) < min_component_size]
    for component in small_components:
        G.remove_nodes_from(component)
    logger.debug(f"Removed discrete components with less than {min_component_size} nodes from graph.")

    return G


def extract_network_scopes(G: nx.Graph):
    scopes = {
        'all': filter_graph(G, min_component_size=3),
    }

    # get world scopes
    for wrld, grp in groupby(sorted((tup for tup in G.nodes(data='world')), key=lambda t: t[1]), key=lambda t: t[1]):
        scopes[wrld] = filter_graph(G.subgraph([n for n, w in grp]), min_component_size=3)

    return scopes


def save_network_gml(scope: str, G: nx.Graph):
    filename = gml_dir / 'family' / f'{scope.replace(" ", "_").lower()}.gml'
    filename.parent.mkdir(parents=True, exist_ok=True)

    nx.write_gml(G, str(filename))
    logger.info(f" GML graph data for {scope} characters written to {filename}")


def save_network_json(scope: str, G: nx.Graph):
    filename = json_dir / 'family' / f'{scope.replace(" ", "_").lower()}.json'
    filename.parent.mkdir(parents=True, exist_ok=True)

    with filename.open(mode='w') as f:
        json.dump(nx.node_link_data(G), f)
    logger.info(f"JSON graph data for {scope} characters written to {filename}")


if __name__ == '__main__':

    graph = create_graph()

    networks = extract_network_scopes(graph)

    for s, ntwk in networks.items():
        save_network_gml(s, ntwk)
        save_network_json(s, ntwk)
