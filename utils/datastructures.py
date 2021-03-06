from collections.abc import MutableMapping
from typing import Any, Dict, Iterable, Iterator, List, Set, Tuple, Union


__all__ = ["CharacterLookup"]


class CharacterLookup(MutableMapping):
    class _Node:
        def __init__(self, key: str):
            self.key: str = key
            self.children: Dict[str, CharacterLookup._Node] = {}
            self.data: Set[Any] = set()

        @property
        def has_data(self) -> bool:
            return bool(self.data)

        def __repr__(self) -> str:
            return f"CharacterLookup._Node({self.key})"

        def __str__(self) -> str:
            return self.key

    def __init__(self):
        self.root = self._Node("")
        self.map = {}

    @staticmethod
    def _process_key(key: Union[slice, str]) -> Tuple[str, bool]:
        if isinstance(key, slice):
            if not all((key.stop is None, key.step is None, isinstance(key.start, str))):
                raise KeyError(key)
            return key.start, True
        else:
            return key, False

    def __getitem__(self, key: str) -> List[Any]:
        if not key:
            raise KeyError(key)

        key, traverse = self._process_key(key)

        if traverse:
            node = self.root
            for char in key:
                if char not in node.children:
                    raise KeyError(key)
                node = node.children[char]
            if not node.children:
                raise KeyError(key)

            items = set()
            stack = [node]
            while stack:
                n = stack.pop()
                if n.has_data:
                    items.update(n.data)
                for _, child in sorted(n.children.items(), reverse=True):
                    stack.append(child)
        else:
            node = self.map.get(key)
            if node is None or not node.has_data:
                raise KeyError(key)
            items = node.data

        return sorted(items, key=str)

    def __setitem__(self, key: str, value: Union[Iterable[Any], Any]) -> None:
        if not key:
            raise KeyError(key)

        key, clear_subtrie = self._process_key(key)

        node = self.root
        for char in key:
            if char not in node.children:
                node.children[char] = self._Node(char)
            node = node.children[char]

        if clear_subtrie:
            node.children.clear()
            node.data.clear()

        if isinstance(value, Iterable):
            node.data.update(value)
        else:
            node.data.add(value)

        if key not in self.map:
            self.map[key] = node

    def __delitem__(self, key: str) -> None:
        if not key:
            raise KeyError(key)

        key, _ = self._process_key(key)

        parent = node = self.root
        for i, char in enumerate(key):
            if char not in node.children:
                raise KeyError(key)
            node = node.children[char]
            if i < len(key) - 1:
                parent = node

        node.children.clear()
        node.data.clear()
        del self.map[node.key]
        del parent.children[node.key]

    def __contains__(self, key: str) -> bool:
        if not key:
            return False

        key, subtrie = self._process_key(key)

        if subtrie:
            node = self.root
            for char in key:
                if char not in node.children:
                    return False
                node = node.children[char]

            stack = [node]
            while stack:
                node = stack.pop()
                if node.has_data:
                    return True
                for _, child in sorted(node.children.items(), reverse=True):
                    stack.append(child)
            return False
        else:
            return key in self.map

    def __len__(self) -> int:
        return len(self.map)

    def __iter__(self) -> Iterator:
        stack = [("", self.root)]
        while stack:
            name, node = stack.pop()
            if node.has_data:
                yield name
            for key, child in sorted(node.children.items(), reverse=True):
                stack.append((name + key, child))

    def __repr__(self) -> str:
        return f"<CharacterLookup: {len(self)} entries>"

    def __str__(self) -> str:
        return "CharacterLookup"
