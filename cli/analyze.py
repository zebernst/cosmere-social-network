from argparse import Namespace

import networks.interactions
from utils.constants import all_keys, book_keys, series_keys


def relatives(args: Namespace):
    print(args)


def interactions(args: Namespace):
    if args.key.lower() == 'list':
        for key in all_keys:
            print('    ' + key)
        print(args)
    else:
        if args.key in book_keys:
            if args.discretize:
                graph = networks.interactions.book_progression(args.key)
            else:
                graph = networks.interactions.book_graph(args.key)

        elif args.key in series_keys:
            if args.discretize:
                graph = networks.interactions.series_progression(args.key)
            else:
                graph = networks.interactions.series_graph(args.key)
        else:
            return

        if args.discretize:
            if args.format.lower() == 'gml':
                print('cannot save discrete graphs in single .gml file.')
                return
            else:
                networks.interactions.save_network_json(args.key + '-discrete', graph)
        else:
            if args.format.lower() in ('gml', 'all'):
                networks.interactions.save_network_gml(args.key, graph)
            elif args.format.lower() in ('json', 'all'):
                networks.interactions.save_network_json(args.key, graph)
