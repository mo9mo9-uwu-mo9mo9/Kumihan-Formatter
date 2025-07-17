"""
ネスト リスト パーサー

階層構造を持つリストの解析機能
Issue #492 Phase 5A - list_parser.py分割
"""

from typing import Dict, List, Optional, Tuple, Union

from .ast_nodes import Node
from .list_parser_core import ListParserCore


class NestedListParser:
    """Parser for nested list structures"""

    def __init__(self, list_parser: ListParserCore):
        self.list_parser = list_parser

    def parse_nested_lists(
        self, lines: List[str], start_index: int
    ) -> Tuple[Optional[Node], int]:
        """
        Parse nested list structures

        Args:
            lines: All lines in the document
            start_index: Index where parsing starts

        Returns:
            tuple: (parsed_node, next_index)
        """
        # TODO: Implement nested list parsing
        # For now, delegate to simple list parser
        line = lines[start_index].strip()
        list_type = self.list_parser.is_list_line(line)

        if list_type == "ul":
            return self.list_parser.parse_unordered_list(lines, start_index)
        elif list_type == "ol":
            return self.list_parser.parse_ordered_list(lines, start_index)
        else:
            # Not a list
            return None, start_index

    def _calculate_indent_level(self, line: str) -> int:
        """Calculate indentation level of a line"""
        return len(line) - len(line.lstrip())

    def _group_by_indent_level(
        self, lines: List[str]
    ) -> Dict[int, List[Tuple[int, str]]]:
        """Group list items by their indentation level"""
        groups: Dict[int, List[Tuple[int, str]]] = {}
        for i, line in enumerate(lines):
            if self.list_parser.is_list_line(line):
                indent = self._calculate_indent_level(line)
                if indent not in groups:
                    groups[indent] = []
                groups[indent].append((i, line))
        return groups
