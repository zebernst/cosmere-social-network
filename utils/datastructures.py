from collections.abc import Iterable, MutableMapping
from typing import Iterator, List, Tuple, Union, Any, Dict, Set

from core.characters import Character


class _TrieNode:
    def __init__(self, key):
        self.key: Any = key
        self.children: Dict[Any, _TrieNode] = {}
        self.data: Set[Any] = set()

    @property
    def has_data(self) -> bool:
        return bool(self.data)

    def __repr__(self) -> str:
        return f"_TrieNode({self.key})"

    def __str__(self) -> str:
        return self.key


class CharacterTrie(MutableMapping):
    def __init__(self):
        self.root = _TrieNode(None)

    @staticmethod
    def _process_key(key: Union[slice, str]) -> Tuple[str, bool]:
        if isinstance(key, slice):
            if key.stop is not None or key.step is not None or not isinstance(key.start, str):
                raise KeyError(key)
            return key.start, True
        else:
            return key, False

    def __getitem__(self, key: str) -> List[Character]:
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

    def __setitem__(self, key: str, value: Union[Iterable[Character], Character]) -> None:
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

    def __contains__(self, key: str) -> bool:
        if not key:
            return False

        key, subtrie = self._process_key(key)

        node = self.root
        for char in key:
            if char not in node.children:
                return False
            node = node.children[char]

        if subtrie:
            stack = [node]
            while stack:
                node = stack.pop()
                if node.has_data:
                    return True
                for _, child in sorted(node.children.items(), reverse=True):
                    stack.append(child)
            return False
        else:
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
