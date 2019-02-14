import argparse
import difflib
import json  # temp
import operator
import time
from itertools import groupby
from datetime import datetime

import colorama

from core.characters import coppermind_query
from core.constants import network_scopes
from utils.paths import coppermind_cache_path, gml_dir, json_dir, log_dir
from utils.caching import load_cache, detect_protocol
from utils.logging import create_logger, get_active_project_loggers, close_file_handlers


logger = create_logger('csn.cli')
colorama.init()


if __name__ == '__main__':

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
                    delta = [rev for rev in old_data + new_data if rev not in old_data or rev not in new_data]

                    if delta:
                        # TEMPORARY - cache wiki changes
                        with (coppermind_cache_path.parent / f'delta_{int(time.time())}.json').open('w') as fp:
                            json.dump(delta, fp, indent=4, sort_keys=True)

                        print()
                        print("wiki changes:", end="\n\n")
                        page_id = operator.itemgetter('pageid')
                        for _, grp in groupby(sorted(delta, key=page_id), key=page_id):
                            grp = list(grp)
                            if len(grp) == 1:
                                char = grp[0]
                                if char in old_data:
                                    print(f"[[{char['title']}]] removed.", end="\n\n")
                                else:
                                    print(f"[[{char['title']}]] added.", end="\n\n")
                            elif len(grp) == 2:
                                if grp[0] in old_data:
                                    old_char, new_char = tuple(grp)
                                else:
                                    new_char, old_char = tuple(grp)

                                if old_char['title'] != new_char['title']:
                                    print(f"[[{old_char['title']}]] renamed to [[{new_char['title']}]].")

                                # diff page content
                                def timestamp_fmt(s: str):
                                    iso_str = s.replace('Z', '+00:00')
                                    return datetime.fromisoformat(iso_str).strftime('%d %b %Y %H:%I:%S')

                                diff = list(difflib.unified_diff(
                                    old_char['revisions'][0]['content'].splitlines(),
                                    new_char['revisions'][0]['content'].splitlines(),
                                    fromfile=old_char['title'],
                                    fromfiledate=timestamp_fmt(old_char['revisions'][0]['timestamp']),
                                    tofile=new_char['title'],
                                    tofiledate=timestamp_fmt(new_char['revisions'][0]['timestamp']),
                                    lineterm=''))

                                if diff:
                                    print(f"[[{new_char['title']}]] modified.")
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
