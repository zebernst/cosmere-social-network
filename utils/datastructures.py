from collections.abc import Iterable, MutableMapping
from typing import Any, Iterator

_empty = object()


class _TrieNode:
    def __init__(self, key):
        self.key = key
        self.children = {}
        self.data = set()

    @property
    def has_data(self):
        return bool(self.data)

    def __repr__(self):
        return f"_TrieNode({self.key})"

    def __str__(self):
        return self.key


class Trie(MutableMapping):
    # todo: implement slicing (w/ start only) a la pygtrie
    def __init__(self):
        self.root = _TrieNode(None)

    @staticmethod
    def _process_key(key):
        if isinstance(key, slice):
            if key.stop is not None or key.step is not None:
                raise KeyError(key)
            return key.start, True
        else:
            return key, False

    def __getitem__(self, key):
        key, get_subtrie = self._process_key(key)

        node = self.root
        for char in key:
            if char not in node.children:
                raise KeyError(key)
            node = node.children[char]

        items = []
        stack = []
        if get_subtrie:


    def __setitem__(self, key, value) -> None:
        key, clear_subtrie = self._process_key(key)

        node = self.root
        for char in key:
            if char not in node.children:
                node.children[char] = _TrieNode(char)
            node = node.children[char]

        if clear_subtrie:
            node.children = {}
            node.data = set()

        if isinstance(value, list):
            node.data = value
        else:
            node.data.add(value)

    def __delitem__(self, v) -> None:
        pass

    def __len__(self) -> int:
        pass

    def __iter__(self) -> Iterator:
        pass


if __name__ == '__main__':
    t = Trie()
    t['this is a string'] = 'abc'
