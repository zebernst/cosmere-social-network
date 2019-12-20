import argparse

import colorama

from cli import analysis, management
from utils.constants import all_keys, worlds
from utils.logs import get_logger


__all__ = ["CommandLineInterface"]

logger = get_logger("csn.cli")
colorama.init(autoreset=True)


class CommandLineInterface:
    class Command:
        # management
        REFRESH = "refresh"
        SHOW = "show"
        CLEANUP = "cleanup"
        DISAMBIGUATE = "disambiguate"

        # analysis
        ANALYZE = "analyze"
        RELATIVES = "relatives"
        INTERACTIONS = "interactions"

    def __init__(self):
        # create initial parser
        self.parser = argparse.ArgumentParser()
        self.parser.set_defaults(func=lambda args: self.parser.print_help())
        subparsers = self.parser.add_subparsers(
            title="commands", description=None, metavar="<command>"
        )

        # management subparsers
        self.parser_refresh = subparsers.add_parser(
            self.Command.REFRESH, help="refresh cached data from source"
        )
        self.parser_refresh.set_defaults(func=management.refresh)
        self.parser_refresh.add_argument(
            "dataset",
            action="store",
            choices=("list", "characters"),
            metavar="<dataset>",
            help="dataset to refresh ('list' for options)",
        )

        self.parser_show = subparsers.add_parser(
            self.Command.SHOW, help="get path of specified data"
        )
        self.parser_show.set_defaults(func=management.show)
        self.parser_show.add_argument(
            "path",
            action="store",
            choices=(
                "list",
                "characters",
                "graphs",
                "gml",
                "json",
                "books",
                "disambiguation",
                "logs",
            ),
            metavar="<component>",
            help="desired component ('list' for options)",
        )

        self.parser_cleanup = subparsers.add_parser(
            self.Command.CLEANUP, help="remove generated files and cached data"
        )
        self.parser_cleanup.set_defaults(func=management.cleanup)
        self.parser_cleanup.add_argument(
            "action",
            nargs="+",
            choices=("all", "caches", "gml", "json", "logs"),
            metavar="<component>",
            help="'all' or any combination of 'caches', 'logs', 'gml' and 'json'",
        )

        self.parser_disambiguate = subparsers.add_parser(
            self.Command.DISAMBIGUATE,
            help="preprocess books and resolve ambiguous character "
            "references prior to analysis",
        )
        self.parser_disambiguate.set_defaults(func=management.disambiguate)
        self.parser_disambiguate.add_argument(
            "key",
            choices=["list"] + all_keys,
            metavar="<text>",
            help="book or series to disambiguate ('list' for options)",
        )

        # analysis subparsers
        self.parse_analyze = subparsers.add_parser(
            self.Command.ANALYZE, help="run network analyses"
        )
        self.parse_analyze.set_defaults(
            func=lambda args: self.parse_analyze.print_help()
        )
        analysis_subparsers = self.parse_analyze.add_subparsers(
            title="analyses", description="network analyses", metavar="<analysis>"
        )

        self.parser_analyze_relatives = analysis_subparsers.add_parser(
            self.Command.RELATIVES,
            help="generate network graphs of related characters",
        )
        self.parser_analyze_relatives.set_defaults(func=analysis.relatives)
        self.parser_analyze_relatives.add_argument(
            "--format",
            choices=("all", "gml", "json"),
            default="all",
            metavar="fmt",
            help="network format ('gml', 'json', or 'all')",
        )
        relative_scope = self.parser_analyze_relatives.add_mutually_exclusive_group()
        relative_scope.add_argument(
            "--world",
            choices=["list"] + list(set(worlds.values())),
            default=None,
            metavar="<world>",
            help="limit analysis to specified world ('list' for options)",
        )
        relative_scope.add_argument(
            "--book",
            choices=["list"] + all_keys,
            default=None,
            metavar="<text>",
            help="limit analysis to specified book or series ('list' for options)",
        )
        relative_scope.add_argument(
            "--family",
            choices=["list", "kholin", "davar", "teoish-royals", "tekiel", "venture"],
            default=None,
            metavar="<family>",
            help="limit analysis to specified family or house ('list' for options)",
        )

        self.parser_analyze_interactions = analysis_subparsers.add_parser(
            self.Command.INTERACTIONS,
            help="generate network graphs of character interactions",
        )
        self.parser_analyze_interactions.set_defaults(func=analysis.interactions)
        self.parser_analyze_interactions.add_argument(
            "key",
            choices=["list", "cosmere"] + all_keys,
            metavar="text",
            help="book or series to analyze ('list' for options)",
        )
        self.parser_analyze_interactions.add_argument(
            "--format",
            choices=("all", "gml", "json"),
            default="all",
            metavar="<fmt>",
            help="network format ('gml', 'json', or 'all', default 'all')",
        )
        self.parser_analyze_interactions.add_argument(
            "--discretize",
            action="store_true",
            default=False,
            help="store each chapter's analysis separately instead of "
            "collating them into a summary analysis of the text",
        )

    def run(self):
        args = self.parser.parse_args()
        args.func(args)
