from collections import Iterable
from typing import Any


class _TrieNode:
    def __init__(self, key: str, data: Any = None):
        self.key = key
        self.children = []
        if isinstance(data, Iterable):
            self.data = list(data)
        elif data is not None:
            self.data = [data]
        else:
            self.data = []

    @property
    def has_data(self):
        return self.data


class Trie:
    # todo: implement len/getitem/setitem/delitem/contains/iter and slicing (w/ start only) a la pygtrie
    def __init__(self):
        self.root = _TrieNode('')

    def __setitem__(self, key: str, value: Any):
        if not key:
            pass  # todo

        node = self.root
        for char in key:
            pass
