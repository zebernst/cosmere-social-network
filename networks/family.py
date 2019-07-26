import json
from itertools import groupby
from typing import Dict, Union

import mwparserfromhell as mwp
import networkx as nx

from core.characters import characters
from utils.logs import create_logger
from utils.paths import gml_dir, json_dir


logger = create_logger('csn.networks.family')


def create_graph() -> nx.OrderedGraph:
    # define relevant fields for analysis
    fields = ('parents', 'siblings', 'spouse', 'children', 'bonded')  # currently: nuclear family only
    unused_fields = ('descendants', 'ancestors', 'family', 'relatives')

    # create graph
    G = nx.OrderedGraph()

    # resolve generator
    relevant_chars = set(c for c in characters if any(f in c.relatives for f in fields))

    # restructure character list into efficient data structures to reduce complexity
    names = {c.name: c for c in relevant_chars}
    monikers = {alias: c for c in relevant_chars for alias in c.monikers}

    # filter on characters who have family info and add nodes to graph
    nodes = {c.id: dict(world=c.world, name=c.name) for c in relevant_chars if c.world is not None}
    G.add_nodes_from(nodes.items())
    logger.debug("Added character nodes to graph.")

    # add edges between relevant nodes
    for char in characters:
        # ignore characters with no family info
        if char.id not in nodes:
            continue

        # loop through character's family connections
        for cxns in (char.relatives[k] for k in fields if k in char.relatives):
            for link in mwp.parse(cxns).filter_wikilinks():
                # sanitize
                relation = link.title.strip_code()
                if "_" in relation:
                    relation = relation.replace('_', ' ')

                # get potential full name
                relation_forename = relation.split(' ')[0]
                char_surname = char.name.split(' ')[-1]

                target = None

                # if direct match found, add edge to graph
                if relation in names:
                    target = names[relation]
                    logger.debug(f'Identified exact target of edge ({char.name}, {relation}).')

                # check if characters share a surname
                elif f"{relation_forename} {char_surname}" in names:
                    target = names[f"{relation_forename} {char_surname}"]
                    logger.debug(f'Identified likely target of edge ({char.name}, {relation}) '
                                 f'to be {target.name} via surname.')

                # check if connection matches any character aliases
                elif relation in monikers:
                    target = monikers[relation]
                    logger.debug(f'Identified likely target of edge ({char.name}, {relation}) '
                                 f'to be {target.name} via alias.')

                # last resort: loop through all characters and match substrings
                else:
                    found = False
                    for name, other in monikers.items():
                        if relation in name:
                            target = other
                            found = True
                            logger.debug(f'Could not confirm target of edge ({char.name}, {relation}), '
                                         f'assuming {target.name}.')
                            break
                    if not found:
                        logger.info(f'Could not identify target of edge ({char.name}, {relation}).')

                # add edge if target is valid
                if target is not None and target.id in nodes:
                    G.add_edge(char.id, target.id)

    return G


def filter_graph(G: nx.Graph, min_component_size: int = 1) -> nx.Graph:
    # create copy of input graph
    G = G.copy()

    # remove discrete components with less than 3 nodes.
    small_components = [c for c in nx.connected_components(G) if len(c) < min_component_size]
    for component in small_components:
        G.remove_nodes_from(component)
    logger.debug(f"Removed discrete components with less than {min_component_size} nodes from graph.")

    return G


def extract_network_scopes(G: Union[nx.Graph, nx.OrderedGraph]) -> Dict[str, Union[nx.Graph, nx.OrderedGraph]]:
    scopes = {
        'all': filter_graph(G, min_component_size=3),
    }

    # get world scopes
    node_attr_world = lambda t: t[1].get('world')
    sorted_nodes = sorted((tup for tup in G.nodes(data=True)), key=node_attr_world)
    for world, grp in groupby(sorted_nodes, key=node_attr_world):
        sg = nx.OrderedGraph()
        sg.add_nodes_from(grp)
        sg.add_edges_from((src, dest) for src, dest in G.edges() if src in sg and dest in sg)
        if sg.size():
            scopes[world] = filter_graph(sg, min_component_size=3)

    return scopes


def save_network_gml(scope: str, G: Union[nx.Graph, nx.OrderedGraph]):
    filename = gml_dir / 'family' / f'{scope.replace(" ", "_").lower()}.gml'
    filename.parent.mkdir(parents=True, exist_ok=True)

    nx.write_gml(G, str(filename))
    logger.info(f" GML graph data for {scope} characters written to {filename}")


def save_network_json(scope: str, G: Union[nx.Graph, nx.OrderedGraph]):
    filename = json_dir / 'family' / f'{scope.replace(" ", "_").lower()}.json'
    filename.parent.mkdir(parents=True, exist_ok=True)

    with filename.open(mode='w') as f:
        json.dump(nx.node_link_data(G), f)
    logger.info(f"JSON graph data for {scope} characters written to {filename}")


# todo : link core.constants.network_scopes and the world attribute together so that saving by scope is truly possible

if __name__ == '__main__':

    graph = create_graph()

    networks = extract_network_scopes(graph)

    for s, ntwk in networks.items():
        save_network_gml(s, ntwk)
        save_network_json(s, ntwk)
