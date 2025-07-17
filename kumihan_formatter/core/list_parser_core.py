"""
リスト パーサー コア

基本的なリスト解析機能（順序付き・順序なしリスト）
Issue #492 Phase 5A - list_parser.py分割
"""

import re
from typing import Tuple

from .ast_nodes import Node, list_item, ordered_list, unordered_list
from .keyword_parser import KeywordParser


class ListParserCore:
    """
    リスト構造パーサー（順序付き・順序なしリスト解析）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#Kumihan記法基本構文（リスト部分）
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - KeywordParser: キーワード付きリスト項目の処理で使用
    - Node: リスト・リスト項目ノードの生成
    - unordered_list, ordered_list, list_item: ファクトリー関数
    - Parser: このクラスを使用する上位パーサー

    責務:
    - "- " および "・" 形式の順序なしリスト解析
    - "1. " 形式の順序付きリスト解析
    - キーワード付きリスト項目の処理（;;;キーワード;;; 記法）
    """

    def __init__(self, keyword_parser: KeywordParser):
        self.keyword_parser = keyword_parser

    def parse_unordered_list(
        self, lines: list[str], start_index: int
    ) -> Tuple[Node, int]:
        """
        Parse an unordered list starting from the given index

        Args:
            lines: All lines in the document
            start_index: Index where list starts

        Returns:
            tuple: (list_node, next_index)
        """
        items = []
        current_index = start_index

        while current_index < len(lines):
            line = lines[current_index].strip()

            # Check if this is a list item
            if not (line.startswith("- ") or line.startswith("・")):
                break

            # Parse the list item
            item_node, consumed_lines = self._parse_list_item(
                lines, current_index, is_ordered=False
            )
            items.append(item_node)
            current_index += consumed_lines

        return unordered_list(items), current_index

    def parse_ordered_list(
        self, lines: list[str], start_index: int
    ) -> Tuple[Node, int]:
        """
        Parse an ordered list starting from the given index

        Args:
            lines: All lines in the document
            start_index: Index where list starts

        Returns:
            tuple: (list_node, next_index)
        """
        items = []
        current_index = start_index

        while current_index < len(lines):
            line = lines[current_index].strip()

            # Check if this is a numbered list item
            if not re.match(r"^\d+\.\s", line):
                break

            # Parse the list item
            item_node, consumed_lines = self._parse_list_item(
                lines, current_index, is_ordered=True
            )
            items.append(item_node)
            current_index += consumed_lines

        return ordered_list(items), current_index

    def _parse_list_item(
        self, lines: list[str], index: int, is_ordered: bool
    ) -> Tuple[Node, int]:
        """
        Parse a single list item

        Args:
            lines: All lines in the document
            index: Index of the list item line
            is_ordered: Whether this is from an ordered list

        Returns:
            tuple: (list_item_node, lines_consumed)
        """
        line = lines[index].strip()

        if is_ordered:
            # Remove number prefix (e.g., "1. ")
            match = re.match(r"^\d+\.\s(.*)$", line)
            if not match:
                return list_item(""), 1
            content = match.group(1)
        else:
            # Remove bullet prefix ("- " or "・")
            if line.startswith("- "):
                content = line[2:]
            elif line.startswith("・"):
                content = line[1:]
            else:
                content = line

        # Check for keyword syntax in list item
        if content.startswith(";;;") and ";;; " in content:
            return self._parse_keyword_list_item(content), 1
        else:
            return list_item(content), 1

    def _parse_keyword_list_item(self, content: str) -> Node:
        """
        Parse a list item with keyword syntax

        Format: ;;;keyword;;; content

        Args:
            content: The content of the list item

        Returns:
            Node: List item node with keyword styling applied
        """
        # Extract keyword and content
        parts = content.split(";;; ", 1)
        if len(parts) != 2:
            return list_item(content)  # Fallback to regular item

        keyword_part = parts[0][3:]  # Remove leading ;;;
        text_content = parts[1]

        # Parse keywords
        keywords, attributes, errors = self.keyword_parser.parse_marker_keywords(
            keyword_part
        )

        if errors or not keywords:
            # If there are errors, create regular list item with error indication
            error_content = (
                f"[ERROR: {'; '.join(errors)}] {text_content}"
                if errors
                else text_content
            )
            return list_item(error_content)

        # Create styled content
        if len(keywords) == 1:
            # Single keyword
            styled_content = self.keyword_parser.create_single_block(
                keywords[0], text_content, attributes
            )
        else:
            # Compound keywords
            styled_content = self.keyword_parser.create_compound_block(
                keywords, text_content, attributes
            )

        return list_item(styled_content)

    def is_list_line(self, line: str) -> str:
        """
        Check if a line starts a list and return the list type

        Args:
            line: Line to check

        Returns:
            str: 'ul' for unordered, 'ol' for ordered, '' for not a list
        """
        line = line.strip()

        if line.startswith("- ") or line.startswith("・"):
            return "ul"
        elif re.match(r"^\d+\.\s", line):
            return "ol"
        else:
            return ""

    def contains_list(self, content: str) -> bool:
        """
        Check if content contains list syntax

        Args:
            content: Content to check

        Returns:
            bool: True if content contains list syntax
        """
        lines = content.split("\n")
        for line in lines:
            if self.is_list_line(line):
                return True
        return False

    def extract_list_items(self, content: str) -> list[str]:
        """
        Extract list items from content

        Args:
            content: Content containing lists

        Returns:
            list[str]: List of item contents
        """
        items = []
        lines = content.split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("- "):
                items.append(line[2:])
            elif line.startswith("・"):
                items.append(line[1:])
            elif re.match(r"^\d+\.\s", line):
                match = re.match(r"^\d+\.\s(.*)$", line)
                if match:
                    items.append(match.group(1))

        return items
