import networkx as nx
import mwparserfromhell as mwp

from characters import characters
from constants import root_dir

if __name__ == '__main__':
    # define relevant fields for analysis
    fields = ('parents', 'siblings', 'spouse', 'children', 'bonded')
    unused_fields = ('descendants', 'ancestors', 'family', 'relatives')

    # create graph
    graph = nx.Graph()

    # restructure character list into efficient data structures to reduce complexity
    # char_dict = {c.name: c for c in characters}
    monikers = {name: c for c in characters for name in c.monikers}

    # filter characters who have family info and add nodes to graph
    nodes = {c.name: dict(world=c.world) for c in characters if any(x in c.info for x in fields)}
    graph.add_nodes_from(nodes.items())

    # add edges between relevant nodes
    for c in characters:
        # ignore characters with no family info
        if c.name not in nodes:
            continue
        curr_node = graph[c.name]

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
                    graph.add_edge(c.name, relation)

                # check if characters share a surname
                elif f"{forename} {surname}" in nodes:
                    graph.add_edge(c.name, f"{forename} {surname}")

                # check if connection matches any character aliases
                elif relation in monikers:
                    graph.add_edge(c.name, monikers[relation].name)

                # last resort: loop through all characters and match substrings
                else:
                    found = False
                    for name in monikers:
                        if relation in name:
                            graph.add_edge(c.name, name)
                            found = True
                            print(c.name, '//', relation, '=', name)
                            break
                    if not found:
                        print(c.name, '//', relation)

    # remove discrete components with less than 3 nodes.
    small_components = [c for c in sorted(nx.connected_components(graph), key=len, reverse=True) if len(c) < 3]
    for component in small_components:
        graph.remove_nodes_from(component)

    nx.write_gml(graph, str(root_dir / 'networks' / 'gml' / 'nuclear_family.gml'))