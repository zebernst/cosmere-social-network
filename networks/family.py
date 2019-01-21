import networkx as nx
import mwparserfromhell as mwp

from characters import characters
from constants import root_dir
from utils.logging import create_logger

logger = create_logger('csn.networks.family')


def create_graph(min_component_size=0):
    # define relevant fields for analysis
    fields = ('parents', 'siblings', 'spouse', 'children', 'bonded')  # currently: nuclear family only
    unused_fields = ('descendants', 'ancestors', 'family', 'relatives')

    # create graph
    G = nx.Graph()

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

                forename = relation.split(' ')[0]
                surname = c.name.split(' ')[-1]

                # if direct match found, add edge to graph
                if relation in nodes:
                    G.add_edge(c.name, relation)
                    logger.debug(f'Identified exact target of edge ({c.name}, {relation}).')

                # check if characters share a surname
                elif f"{forename} {surname}" in nodes:
                    G.add_edge(c.name, f"{forename} {surname}")
                    logger.debug(f'Identified likely target of edge ({c.name}, {relation}) '
                                 f'to be {forename} {surname} via surname.')

                # check if connection matches any character aliases
                elif relation in monikers:
                    G.add_edge(c.name, monikers[relation].name)
                    logger.debug(f'Identified likely target of edge ({c.name}, {relation}) '
                                 f'to be {monikers[relation].name} via alias.')

                # last resort: loop through all characters and match substrings
                else:
                    found = False
                    for name in monikers:
                        if relation in name:
                            G.add_edge(c.name, name)
                            found = True
                            logger.debug(f'Could not confirm target of edge ({c.name}, {relation}), assuming {name}.')
                            break
                    if not found:
                        logger.info(f'Could not identify target of edge ({c.name}, {relation}).')

    # remove discrete components with less than 3 nodes.
    small_components = [c for c in nx.connected_components(G) if len(c) < min_component_size]
    for component in small_components:
        G.remove_nodes_from(component)
    logger.debug("Identified and trimmed discrete components deemed too small for analysis.")

    return G


if __name__ == '__main__':

    graph = create_graph(min_component_size=3)

    filename = root_dir / 'networks' / 'gml' / 'family.gml'
    nx.write_gml(graph, str(filename))
    logger.info(f"GML graph written to {filename}")
