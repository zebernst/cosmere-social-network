import argparse
import difflib
import json  # temp
import operator
import time  # temp
from datetime import datetime
from itertools import groupby

import colorama

from core.characters import coppermind_query
from utils.caching import detect_protocol, load_cache
from utils.logging import close_file_handlers, create_logger, get_active_project_loggers
from utils.paths import coppermind_cache_path, gml_dir, json_dir, log_dir
from utils.wiki import extract_info


logger = create_logger('csn.cli')
colorama.init()


# define commands
def data_refresh(arg: str):
    if any(dataset == arg.lower() for dataset in ('coppermind', 'characters')):
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
            delta = [rev for rev in old_data + new_data if rev not in old_data or rev not in new_data]

            if delta:
                # TEMPORARY - cache wiki changes
                time_str = datetime.now().isoformat(timespec="seconds")
                with (coppermind_cache_path.parent / f'delta_{time_str}.json').open('w') as fp:
                    json.dump(delta, fp, indent=4, sort_keys=True, default=str)

                print()
                print("wiki changes:", end="\n\n")
                page_id = operator.itemgetter('pageid')
                for _, grp in groupby(sorted(delta, key=page_id), key=page_id):
                    grp = list(grp)
                    if len(grp) == 1:
                        char = extract_info(grp[0])
                        if char in old_data:
                            print(f"[[{char['title']}]] removed.", end="\n\n")
                        else:
                            print(f"[[{char['title']}]] added.", end="\n\n")
                    elif len(grp) == 2:
                        if grp[0] in old_data:
                            old, new = tuple(extract_info(r) for r in grp)
                        else:
                            new, old = tuple(extract_info(r) for r in grp)

                        if old['title'] != new['title']:
                            print(f"[[{old['title']}]] renamed to [[{new['title']}]].")

                        # diff page content
                        date_str = "%d %b %Y %H:%I:%S"
                        diff = list(difflib.unified_diff(
                            old['content'].splitlines(),
                            new['content'].splitlines(),
                            fromfile=old['title'],
                            fromfiledate=old['timestamp'].strftime(date_str) if old['timestamp'] else '',
                            tofile=new['title'],
                            tofiledate=new['timestamp'].strftime(date_str) if new['timestamp'] else '',
                            lineterm=''))

                        if diff:
                            print(f"[[{new['title']}]] modified.")
                            print("content diff:")
                            for line in diff:
                                if line.startswith('-') and not line.startswith('---'):
                                    print(f"{colorama.Fore.RED}{line}{colorama.Fore.RESET}")
                                elif line.startswith('+') and not line.startswith('+++'):
                                    print(f"{colorama.Fore.GREEN}{line}{colorama.Fore.RESET}")
                                elif line.startswith('@@'):
                                    print(f"{colorama.Fore.CYAN}{line}{colorama.Fore.RESET}")
                                elif line.startswith(' '):
                                    print(f"{colorama.Style.DIM}{line}{colorama.Style.NORMAL}")
                                else:
                                    print(line)
                            print(end="\n\n")
            else:
                print("no changes detected in refreshed data.")

        # no data cached
        else:
            data = coppermind_query()
            print("character data refreshed from coppermind.net.")


def data_path(arg: str):
    if any(ds == arg.lower() for ds in ('coppermind', 'characters')):
        print("coppermind.net data located at", coppermind_cache_path)


def cleanup():
    # remove cached data
    if coppermind_cache_path.is_file():
        coppermind_cache_path.unlink()
    print('Removed cached coppermind.net data')

    # remove gml data
    for file in gml_dir.glob('**/*.gml'):
        file.unlink()
    print('Removed generated GML network data.')

    # remove json data
    for file in json_dir.glob('**/*.json'):
        file.unlink()
    print('Removed generated JSON network data.')

    # remove log files
    for l in get_active_project_loggers():
        close_file_handlers(l)
    for file in log_dir.glob('**/*.log'):
        file.unlink()
    print('Removed log files.')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    subparser_var = 'cmd'
    subparsers = parser.add_subparsers(title='subcommands',
                                       description=None,
                                       dest=subparser_var)

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
    if all(v is None for arg, v in args.__dict__.items() if arg != subparser_var):
        p = parsers.get(args.cmd)
        p.print_help()
        p.exit()

    # handle args
    if args.cmd == 'data':
        if args.refresh:
            data_refresh(args.refresh)

        elif args.path:
            data_path(args.path)

    elif args.cmd == 'network':
        # todo
        pass

    elif args.cmd is None:
        if args.cleanup:
            cleanup()
