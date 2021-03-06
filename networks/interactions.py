import json
from itertools import combinations
from typing import Union

import networkx as nx
import yaml
from tqdm import tqdm

from core.characters import characters, lookup
from core.config import InteractionNetworkConfig
from utils.constants import book_keys, titles
from utils.disambiguation import check_position, verify_presence
from utils.epub import tokenize_chapters
from utils.exceptions import (
    NoDisambiguationFoundError,
    IncompleteDisambiguationError,
    InvalidDisambiguationError,
)
from utils.logs import get_logger
from utils.paths import disambiguation_dir, gml_dir, json_dir
from utils.simpletypes import CharacterOccurrence


__all__ = [
    "book_graph",
    "series_graph",
    "discrete_book_graph",
    "discrete_series_graph",
    "cosmere_graph",
    "save_network_gml",
    "save_network_json",
]

logger = get_logger("csn.networks.interactions")

RUN_SIZE = InteractionNetworkConfig.run_size

nodes = {c.id: c.properties for c in characters}
logger.debug("Created dictionary of nodes.")


def save_disambiguation(book: str, disambiguation: dict):
    with (disambiguation_dir / book).with_suffix(".yml").open(mode="w") as f:
        yaml.dump(
            disambiguation, f, yaml.Dumper, default_flow_style=False, sort_keys=False
        )


def load_disambiguation(key: str):
    disambiguation_path = (disambiguation_dir / key).with_suffix(".yml")
    if not disambiguation_path.exists():
        msg = f"No disambiguation file found for {key}. Please run disambiguation  before analyzing text."
        raise NoDisambiguationFoundError(msg)
    with disambiguation_path.open(mode="r") as f:
        disambiguation = yaml.load(f, yaml.Loader)
        if not isinstance(disambiguation, dict):
            msg = f"Invalid disambiguation found for {key}. Please run disambiguation again."
            raise InvalidDisambiguationError(msg)

    return disambiguation


def combine_edges(G: nx.Graph, other: nx.Graph):
    for u, v, w in other.edges(data="weight"):
        if G.has_edge(u, v):
            G[u][v]["weight"] += w
        else:
            G.add_edge(u, v, weight=w)


def _chapter_graph(key: str, tokens: list, disambiguation: dict):
    G = nx.Graph()
    G.add_nodes_from(nodes.items())

    idx = 0
    while idx < len(tokens):
        i = 0
        found = []
        run = " ".join(tokens[idx : min(len(tokens), idx + RUN_SIZE)])
        tokens_remaining = len(tokens) - idx
        while i < min(RUN_SIZE, tokens_remaining):
            char = None
            pos = idx + i

            this_token = tokens[pos]
            next_token = tokens[pos + 1] if pos + 1 < len(tokens) else ""
            third_token = tokens[pos + 2] if pos + 2 < len(tokens) else ""
            two_tokens = this_token + " " + next_token
            next_two_tokens = next_token + " " + third_token
            three_tokens = two_tokens + " " + third_token

            if three_tokens in lookup:
                matches = [
                    c
                    for c in lookup[three_tokens]
                    if verify_presence(key, c, three_tokens)
                ]
                if len(matches) > 1:
                    char = check_position(disambiguation, pos)
                elif len(matches) == 1:
                    char = matches[0]
                else:
                    char = None
                i += 3

            elif two_tokens in lookup:
                matches = [
                    c for c in lookup[two_tokens] if verify_presence(key, c, two_tokens)
                ]
                if len(matches) > 1:
                    char = check_position(disambiguation, pos)
                elif len(matches) == 1:
                    char = matches[0]
                else:
                    char = None
                i += 2

            elif this_token in titles:
                if next_token not in lookup and next_two_tokens not in lookup:
                    char = check_position(disambiguation, pos)
                i += 1

            elif this_token in lookup:
                matches = [
                    c for c in lookup[this_token] if verify_presence(key, c, this_token)
                ]
                if len(matches) > 1:
                    char = check_position(disambiguation, pos)
                elif len(matches) == 1:
                    char = matches[0]
                else:
                    char = None
                i += 1

            else:
                i += 1
                continue

            if char is not None:
                found.append(CharacterOccurrence(i, char))

        # advance past first found character
        if len(found) >= 2:
            delta = found[0].pos + 1

        # advance until only character is at beginning of run (max threshold)
        elif len(found) == 1:
            delta = found[0].pos if found[0].pos > 0 else 1

        # skip run if no chars found
        else:
            delta = RUN_SIZE - 1

        chars = set(co.char for co in found)
        if len(chars) > 1:
            for u, v in combinations(chars, r=2):
                if G.has_edge(u.id, v.id):
                    G[u.id][v.id]["weight"] += 1
                else:
                    G.add_edge(u.id, v.id, weight=1)

                logger.debug(
                    f'Added edge ({u.name} #{u.id}, {v.name} #{v.id}) from run "{run}"'
                )

        idx += delta

    G.remove_nodes_from(list(nx.isolates(G)))
    return G


def book_graph(
    book: str, min_weight: int = InteractionNetworkConfig.default_min_weight
):
    G = nx.Graph()
    G.add_nodes_from(nodes.items())

    disambiguation = load_disambiguation(book)
    with tqdm(
        list(tokenize_chapters(book)), desc=f"Analyzing {book}: ", unit=" chapters"
    ) as book_pbar:
        for chapter, tokens in book_pbar:
            if chapter not in disambiguation:
                msg = f"{book}:{chapter} not found in disambiguation. Please run disambiguation again."
                raise IncompleteDisambiguationError(msg)
            book_pbar.set_postfix(chapter=chapter)
            sG = _chapter_graph(book, tokens, disambiguation[chapter])
            combine_edges(G, sG)

    G.remove_edges_from(
        [
            (u, v)
            for (u, v, w) in G.edges(data="weight")
            if w < min_weight and u != 13 and v != 13  # Hoid
        ]
    )
    G.remove_nodes_from(list(nx.isolates(G)))
    return G


def series_graph(series: str):
    G = nx.Graph()
    G.add_nodes_from(nodes.items())

    for book in (b for b in book_keys if b.startswith(series)):
        sG = book_graph(book, min_weight=0)
        combine_edges(G, sG)

    return G


def cosmere_graph():
    G = nx.Graph()
    G.add_nodes_from(nodes.items())

    for book in book_keys:
        sG = book_graph(book, min_weight=0)
        combine_edges(G, sG)

    return G


def discrete_book_graph(book: str):
    with (disambiguation_dir / book).with_suffix(".yml").open(mode="r") as f:
        disambiguation = yaml.load(f, yaml.Loader)
        if disambiguation is None:
            disambiguation = {}

    return [
        _chapter_graph(book, tokens, disambiguation)
        for chapter, tokens in tokenize_chapters(book)
    ]


def discrete_series_graph(series: str):
    chapters = []
    for book in (b for b in book_keys if b.startswith(series)):
        chapters.extend(discrete_book_graph(book))

    return chapters


def save_network_gml(key: str, G: Union[nx.Graph, nx.OrderedGraph]):
    filename = gml_dir / "interactions" / f"{key}.gml"
    filename.parent.mkdir(parents=True, exist_ok=True)

    nx.write_gml(G, str(filename), stringizer=lambda p: str(p) if p else "null")
    logger.info(f"GML  graph data for {key} characters written to {filename}")


def save_network_json(key: str, G: Union[nx.Graph, nx.OrderedGraph]):
    filename = json_dir / "interactions" / f"{key}.json"
    filename.parent.mkdir(parents=True, exist_ok=True)

    with filename.open(mode="w") as f:
        json.dump(nx.node_link_data(G), f)
    logger.info(f"JSON graph data for {key} characters written to {filename}")
