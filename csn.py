import argparse

from core.characters import coppermind_query
from core.constants import network_scopes
from utils.paths import coppermind_cache_path, gml_dir, json_dir
from utils.caching import load_cache, detect_protocol
from utils.logging import create_logger

if __name__ == '__main__':

    logger = create_logger('csn.cli')

    parser = argparse.ArgumentParser()
    subparser_attr = 'cmd'
    subparsers = parser.add_subparsers(title='subcommands',
                                       description=None,
                                       dest=subparser_attr)

    # characters
    data_parser = subparsers.add_parser("data", help='manage data')
    data_group = data_parser.add_mutually_exclusive_group()
    data_group.add_argument("--refresh", metavar='DATASET', action='store',
                            help='refresh specified data cache from source')
    data_group.add_argument("--path", metavar='DATASET', action='store',
                            help='print path of specified data')

    # networks
    network_parser = subparsers.add_parser("network", help='run a network analysis')
    network_optional = network_parser._action_groups.pop()  # re-order argument groups
    network_required = network_parser.add_argument_group('required named arguments')
    network_required.add_argument("-t", "--type", action='store', required=True,
                                  help='network analysis type')
    network_optional.add_argument("-s", "--scope", action='store',
                                  help='specify network scope')
    network_parser._action_groups.append(network_optional)

    # utility
    parser.add_argument("--cleanup", action='store_true', default='all',
                        help='remove generated files and cached data')

    args = parser.parse_args()

    # print parser help if no arguments provided
    parsers = {None: parser, 'data': data_parser, 'network': network_parser}
    if all(v is None for arg, v in args.__dict__.items() if arg != subparser_attr):
        p = parsers.get(args.cmd)
        p.print_help()
        p.exit()

    # handle args
    if args.cmd == 'data':
        if args.refresh:
            if any(ds in args.refresh.lower() for ds in ('coppermind', 'characters')):
                # remove cache and re-download data
                logger.debug("Refreshing coppermind.net character data.")

                # cache already exists
                if coppermind_cache_path.is_file():
                    old_data = load_cache(coppermind_cache_path, protocol=detect_protocol(coppermind_cache_path))
                    coppermind_cache_path.unlink()
                    logger.debug("Cache removed.")
                    new_data = coppermind_query()
                    print("character data refreshed from coppermind.net.")

                    # display changed results
                    delta = [r for r in old_data + new_data if r not in old_data or r not in new_data]
                    if delta:
                        print("changed items:")
                        print(delta)
                    else:
                        print("no changes detected in refreshed data.")

                # no data cached
                else:
                    data = coppermind_query()
                    print("character data refreshed from coppermind.net.")

        elif args.path:
            if any(ds in args.path.lower() for ds in ('coppermind', 'characters')):
                print(args.path, "located at", coppermind_cache_path)

    elif args.cmd == 'network':
        pass

    elif args.cmd is None:
        if args.cleanup:
            # remove cached data
            if coppermind_cache_path.is_file():
                coppermind_cache_path.unlink()
                logger.debug(f'Removed {coppermind_cache_path}.')
                print('Removed cached coppermind.net data')

            # remove gml data
            for file in gml_dir.glob('**/*.gml'):
                file.unlink()
                logger.debug(f'Removed {file}.')
            print('Removed generated GML network data.')

            # remove json data
            for file in json_dir.glob('**/*.json'):
                file.unlink()
                logger.debug(f'Removed {file}.')
            print('Removed generated JSON network data.')
