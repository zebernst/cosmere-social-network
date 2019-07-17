from collections.abc import Iterable, MutableMapping
from typing import Any, Iterator, Set


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


class CharacterTrie(MutableMapping):
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

    def __getitem__(self, key: str):
        if not key:
            raise KeyError(key)

        key, get_subtrie = self._process_key(key)

        node = self.root
        for char in key:
            if char not in node.children:
                raise KeyError(key)
            node = node.children[char]
        if not node.has_data and not get_subtrie:
            raise KeyError(key)

        if get_subtrie:
            items = []
            stack = [node]
            while stack:
                n = stack.pop()
                if n.has_data:
                    items.extend(e for e in n.data)
                for _, child in sorted(n.children.items(), reverse=True):
                    stack.append(child)
        else:
            items = [e for e in node.data]

        return sorted(items, key=str)

    def __setitem__(self, key: str, value) -> None:
        if not key:
            raise KeyError(key)

        key, clear_subtrie = self._process_key(key)

        node = self.root
        for char in key:
            if char not in node.children:
                node.children[char] = _TrieNode(char)
            node = node.children[char]

        if clear_subtrie:
            node.children.clear()
            node.data.clear()

        if isinstance(value, Iterable):
            node.data.update(value)
        else:
            node.data.add(value)

    def __delitem__(self, key: str) -> None:
        if not key:
            raise KeyError(key)

        key, _ = self._process_key(key)

        node = self.root
        for char in key:
            if char not in node.children:
                raise KeyError(key)
            node = node.children[char]

        node.children.clear()
        node.data.clear()

    def __contains__(self, key: str):
        if not key:
            return False

        key, subtrie = self._process_key(key)
        if subtrie:
            raise KeyError(key)

        node = self.root
        for char in key:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.has_data

    def __len__(self) -> int:
        size = 0
        stack = [self.root]
        while stack:
            node = stack.pop()
            if node.has_data:
                size += 1
            for _, child in sorted(node.children.items(), reverse=True):
                stack.append(child)
        return size

    def __iter__(self) -> Iterator:
        stack = [('', self.root)]
        while stack:
            name, node = stack.pop()
            if node.has_data:
                yield name
            for key, child in sorted(node.children.items(), reverse=True):
                stack.append((name + key, child))
