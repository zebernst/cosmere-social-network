from argparse import Namespace


__all__ = ["relatives", "interactions"]


def relatives(args: Namespace):
    print(args)


def interactions(args: Namespace):
    import networks.interactions
    from utils.constants import all_keys, book_keys, series_keys

    if args.key.lower() == "list":
        print("    cosmere")
        for key in all_keys:
            print("    " + key)
        print(args)
    else:
        if args.key == "cosmere":
            if args.discretize:
                print("Chapter-by-chapter graphs cannot be produced across series!")
                return
            else:
                graph = networks.interactions.cosmere_graph()
        elif args.key in book_keys:
            if args.discretize:
                graph = networks.interactions.discrete_book_graph(args.key)
            else:
                graph = networks.interactions.book_graph(args.key)

        elif args.key in series_keys:
            if args.discretize:
                graph = networks.interactions.discrete_series_graph(args.key)
            else:
                graph = networks.interactions.series_graph(args.key)
        else:
            return

        if args.discretize:
            if args.format.lower() == "gml":
                print("cannot save discrete graphs in single .gml file.")
                return
            else:
                networks.interactions.save_network_json(args.key + "-discrete", graph)
        else:
            if args.format.lower() in ("gml", "all"):
                networks.interactions.save_network_gml(args.key, graph)
            if args.format.lower() in ("json", "all"):
                networks.interactions.save_network_json(args.key, graph)
