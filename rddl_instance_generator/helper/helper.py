from dataclasses import dataclass, field
from typing import Dict, List


def find_shortest_unique_prefix(strings: List[str]) -> Dict[str, str]:
    unique_prefixes: Dict[str, str] = {}

    trie = Trie()
    trie.update(strings=strings)

    for string in strings:
        unique_prefix = trie.get_shortest_unique_prefix(string=string)
        unique_prefixes[string] = unique_prefix

    return unique_prefixes


@dataclass
class TrieNode:
    children: Dict[str, "TrieNode"] = field(default_factory=dict)
    count: int = 0


@dataclass
class Trie:
    root: TrieNode = field(default_factory=TrieNode)

    def add(self, string: str):
        curr_node = self.root
        for char in string:
            if char not in curr_node.children:
                curr_node.children[char] = TrieNode()
            curr_node = curr_node.children[char]
            curr_node.count += 1
        curr_node.count += 1

    def update(self, strings: List[str]):
        for string in strings:
            self.add(string)

    def get_shortest_unique_prefix(self, string: str) -> str:
        curr_node = self.root
        prefix = ""
        for char in string:
            prefix += char
            curr_node = curr_node.children[char]
            if curr_node.count == 1:
                return prefix
        return prefix
