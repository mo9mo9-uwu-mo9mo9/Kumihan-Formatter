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
    - キーワード付きリスト項目の処理（;;;記法は削除されました）
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
            if not (
                line.startswith("- ")
                or line.startswith("・")
                or line.startswith("* ")
                or line.startswith("+ ")
            ):
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
        Parse a single list item with support for nested content and multi-line items

        Args:
            lines: All lines in the document
            index: Index of the list item line
            is_ordered: Whether this is from an ordered list

        Returns:
            tuple: (list_item_node, lines_consumed)
        """
        line = lines[index].strip()
        lines_consumed = 1

        if is_ordered:
            # Remove number prefix (e.g., "1. ")
            match = re.match(r"^\d+\.\s(.*)$", line)
            if not match:
                return list_item(""), 1
            content = match.group(1)
        else:
            # Remove bullet prefix ("- ", "・", "* ", or "+ ")
            if line.startswith("- "):
                content = line[2:]
            elif line.startswith("・"):
                content = line[1:]
            elif line.startswith("* "):
                content = line[2:]
            elif line.startswith("+ "):
                content = line[2:]
            else:
                content = line

        # Collect multi-line content and nested items
        collected_content = [content] if content.strip() else []
        current_index = index + 1

        while current_index < len(lines):
            next_line = lines[current_index].strip()
            
            # Stop at empty line
            if not next_line:
                break
                
            # Handle nested list items (with additional indentation)
            original_line = lines[current_index]
            
            # Stop at next list item at same level (not indented)
            if self.is_list_line(next_line) and not (original_line.startswith("  ") or original_line.startswith("\t")):
                break
            if original_line.startswith("  ") or original_line.startswith("\t"):
                # This is indented content - could be nested list or continuation
                indented_content = original_line.lstrip()
                
                # Check if it's a nested list item
                if self.is_list_line(indented_content):
                    # Parse nested list (collect all items at same level)
                    nested_list_type = self.is_list_line(indented_content)
                    if nested_list_type == "ul":
                        nested_list, consumed = self._parse_nested_unordered_list(lines, current_index)
                    else:
                        nested_list, consumed = self._parse_nested_ordered_list(lines, current_index)
                    
                    collected_content.append(nested_list)
                    current_index += consumed
                    lines_consumed += consumed
                    
                    # Skip processing any further nested items at this level
                    # as they were already consumed by the nested list parser
                    continue
                else:
                    # Regular indented continuation
                    collected_content.append(indented_content)
            else:
                # Regular continuation line
                collected_content.append(next_line)
            
            current_index += 1
            lines_consumed += 1

        # Process inline notation in all content
        if len(collected_content) == 1 and isinstance(collected_content[0], str):
            # Single line content
            processed_content = self.keyword_parser._process_inline_keywords(collected_content[0])
        else:
            # Multi-line or mixed content
            processed_parts = []
            for part in collected_content:
                if isinstance(part, str):
                    processed_parts.append(self.keyword_parser._process_inline_keywords(part))
                else:
                    # Nested node (list, etc.)
                    processed_parts.append(part)
            processed_content = processed_parts

        return list_item(processed_content), lines_consumed

    def _parse_nested_unordered_list(
        self, lines: list[str], start_index: int
    ) -> Tuple[Node, int]:
        """
        Parse a nested unordered list starting from the given index
        
        Args:
            lines: All lines in the document
            start_index: Index where nested list starts
            
        Returns:
            tuple: (nested_list_node, lines_consumed)
        """
        items = []
        current_index = start_index
        lines_consumed = 0
        base_indent = self._get_line_indent(lines[start_index])

        while current_index < len(lines):
            line = lines[current_index].strip()
            original_line = lines[current_index]
            
            # Stop if line is not indented at same level or is empty
            if not line or self._get_line_indent(original_line) < base_indent:
                break
                
            # Stop if this is not a list item at this indent level
            if self._get_line_indent(original_line) == base_indent:
                if not self.is_list_line(line):
                    break
                    
                # Parse this nested list item
                item_node, consumed = self._parse_list_item(lines, current_index, is_ordered=False)
                items.append(item_node)
                current_index += consumed
                lines_consumed += consumed
            else:
                # Skip deeper nested content (will be handled by recursive calls)
                current_index += 1
                lines_consumed += 1

        return unordered_list(items), lines_consumed
    
    def _parse_nested_ordered_list(
        self, lines: list[str], start_index: int
    ) -> Tuple[Node, int]:
        """
        Parse a nested ordered list starting from the given index
        
        Args:
            lines: All lines in the document
            start_index: Index where nested list starts
            
        Returns:
            tuple: (nested_list_node, lines_consumed)
        """
        items = []
        current_index = start_index
        lines_consumed = 0
        base_indent = self._get_line_indent(lines[start_index])

        while current_index < len(lines):
            line = lines[current_index].strip()
            original_line = lines[current_index]
            
            # Stop if line is not indented at same level or is empty
            if not line or self._get_line_indent(original_line) < base_indent:
                break
                
            # Stop if this is not a list item at this indent level  
            if self._get_line_indent(original_line) == base_indent:
                if not re.match(r"^\s*\d+\.\s", original_line):
                    break
                    
                # Parse this nested list item
                item_node, consumed = self._parse_list_item(lines, current_index, is_ordered=True)
                items.append(item_node)
                current_index += consumed
                lines_consumed += consumed
            else:
                # Skip deeper nested content (will be handled by recursive calls)
                current_index += 1
                lines_consumed += 1

        return ordered_list(items), lines_consumed
    
    def _get_line_indent(self, line: str) -> int:
        """
        Get the indentation level of a line
        
        Args:
            line: Line text to analyze
            
        Returns:
            int: Number of leading spaces (tabs count as 4 spaces)
        """
        indent = 0
        for char in line:
            if char == ' ':
                indent += 1
            elif char == '\t':
                indent += 4
            else:
                break
        return indent

    def _parse_keyword_list_item(self, content: str) -> Node:
        """
        Parse a list item with keyword syntax

        ;;;記法は削除されました（Phase 1）
        この機能は新記法で置き換えられます
        """
        return list_item(content)

    def is_list_line(self, line: str) -> str:
        """
        Check if a line starts a list and return the list type

        Args:
            line: Line to check

        Returns:
            str: 'ul' for unordered, 'ol' for ordered, '' for not a list
        """
        line = line.strip()

        # Check for unordered list markers with proper spacing
        # Note: ・ doesn't require a space after it
        if (
            line.startswith("- ")
            or line.startswith("・")
            or line.startswith("* ")
            or line.startswith("+ ")
        ):
            # Special case: ensure - has a space after it
            if line.startswith("-") and not line.startswith("- "):
                return ""
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
            elif line.startswith("* "):
                items.append(line[2:])
            elif line.startswith("+ "):
                items.append(line[2:])
            elif re.match(r"^\d+\.\s", line):
                match = re.match(r"^\d+\.\s(.*)$", line)
                if match:
                    items.append(match.group(1))

        return items