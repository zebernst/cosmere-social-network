import argparse

from utils.paths import coppermind_cache_path
from core.constants import network_scopes

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands',
                                       description=None,
                                       dest='cmd')

    # characters
    data_parser = subparsers.add_parser("data", help='manage data')
    data_group = data_parser.add_mutually_exclusive_group()
    data_group.add_argument("--refresh", metavar='DATASET', action='store',
                            help='refresh specified data cache from source')
    data_group.add_argument("--path", metavar='DATASET', action='store',
                            help='print path of specified data')

    # networks
    network_parser = subparsers.add_parser("network", help='run a network analysis')
    network_optional = network_parser._action_groups.pop()
    network_required = network_parser.add_argument_group('required named arguments')
    network_required.add_argument("-t", "--type", action='store', required=True,
                                  help='network analysis type')
    network_optional.add_argument("-s", "--scope", action='store',
                                  help='specify network scope')
    network_parser._action_groups.append(network_optional)

    # utility
    parser.add_argument("--cleanup", action='store', default='all',
                        help='remove generated files, logs, and cached data')

    args = parser.parse_args()

    # print parser help if no arguments provided
    parsers = {None: parser, 'data': data_parser, 'network': network_parser}
    if all(v is None for a, v in args.__dict__.items() if a != 'cmd'):
        p = parsers.get(args.cmd)
        p.print_help()
        p.exit()

    # handle args
    if args.cmd == 'data':
        if args.refresh:
            if any(ds in args.refresh.lower() for ds in ('coppermind', 'characters')):
                pass
        elif args.path:
            if any(ds in args.path.lower() for ds in ('coppermind', 'characters')):
                print(args.path, "located at", coppermind_cache_path)

    elif args.cmd == 'network':
        pass
