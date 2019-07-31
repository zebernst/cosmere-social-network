import difflib
import operator
from argparse import Namespace
from datetime import datetime
from itertools import groupby

import colorama

from utils.caching import detect_protocol, load_cache
from utils.logs import close_file_handlers, get_logger, get_active_project_loggers
from utils.paths import coppermind_cache_path, gml_dir, json_dir, log_dir
from utils.wiki import coppermind_query, extract_relevant_info


logger = get_logger('csn.cli')


def refresh(args: Namespace):
    if args.dataset.lower() == 'list':
        print('    characters                   refreshes the character data from coppermind.net')
    else:
        if args.dataset.lower() in ('coppermind', 'characters', 'wiki'):
            # remove cache and re-download data
            logger.info("Refreshing coppermind.net character data.")

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
                    fp = (log_dir / 'deltas' / f'{time_str}.log').open('w')

                    print()
                    print("wiki changes:", end="\n\n")
                    page_id = operator.itemgetter('pageid')
                    for _, grp in groupby(sorted(delta, key=page_id), key=page_id):
                        grp = list(grp)
                        if len(grp) == 1:
                            char = extract_relevant_info(grp[0])
                            if char in old_data:
                                print(f"[[{char['title']}]] removed.", end="\n\n")
                                fp.write(f"[[{char['title']}]] removed.\n\n")
                            else:
                                print(f"[[{char['title']}]] added.", end="\n\n")
                                fp.write(f"[[{char['title']}]] added.\n\n")
                        elif len(grp) == 2:
                            if grp[0] in old_data:
                                old, new = tuple(extract_relevant_info(r) for r in grp)
                            else:
                                new, old = tuple(extract_relevant_info(r) for r in grp)

                            if old['title'] != new['title']:
                                print(f"[[{old['title']}]] renamed to [[{new['title']}]].")
                                fp.write(f"[[{old['title']}]] renamed to [[{new['title']}]].\n")

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
                                fp.write(f"[[{new['title']}]] modified.\ncontent diff:\n")
                                fp.writelines(f"{s}\n" for s in diff)
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
                                fp.write("\n\n")
                    fp.close()
                else:
                    print("no changes detected in refreshed data.")

            # no data cached
            else:
                data = coppermind_query()
                print("character data refreshed from coppermind.net.")


def show(args: Namespace):
    if any(ds == args.path.lower() for ds in ('coppermind', 'characters')):
        print("Cached coppermind.net is data located at", coppermind_cache_path)


def cleanup(args: Namespace):
    # remove cached data
    if 'caches' in args.action or 'all' in args.action:
        if coppermind_cache_path.is_file():
            coppermind_cache_path.unlink()
        print('Removed cached coppermind.net data')

    # remove gml data
    if 'gml' in args.action or 'all' in args.action:
        for file in gml_dir.glob('**/*.gml'):
            file.unlink()
        print('Removed generated GML network data.')

    # remove json data
    if 'json' in args.action or 'all' in args.action:
        for file in json_dir.glob('**/*.json'):
            file.unlink()
        print('Removed generated JSON network data.')

    # remove log files
    if 'logs' in args.action or 'all' in args.action:
        for l in get_active_project_loggers().values():
            close_file_handlers(l)
        for file in log_dir.glob('**/*.log'):
            file.unlink()
        print('Removed log files.')
