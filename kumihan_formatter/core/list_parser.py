"""List parsing utilities for Kumihan-Formatter

This module handles the parsing of both unordered and ordered lists,
including keyword-enhanced list items.
"""

import re
from typing import List, Optional, Tuple, Dict

from .ast_nodes import Node, NodeBuilder, unordered_list, ordered_list, list_item
from .keyword_parser import KeywordParser


class ListParser:
    """Parser for list structures (ordered and unordered)"""
    
    def __init__(self, keyword_parser: KeywordParser):
        self.keyword_parser = keyword_parser
    
    def parse_unordered_list(self, lines: List[str], start_index: int) -> Tuple[Node, int]:
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
            if not (line.startswith('- ') or line.startswith('・')):
                break
            
            # Parse the list item
            item_node, consumed_lines = self._parse_list_item(lines, current_index, is_ordered=False)
            items.append(item_node)
            current_index += consumed_lines
        
        return unordered_list(items), current_index
    
    def parse_ordered_list(self, lines: List[str], start_index: int) -> Tuple[Node, int]:
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
            if not re.match(r'^\d+\.\s', line):
                break
            
            # Parse the list item
            item_node, consumed_lines = self._parse_list_item(lines, current_index, is_ordered=True)
            items.append(item_node)
            current_index += consumed_lines
        
        return ordered_list(items), current_index
    
    def _parse_list_item(self, lines: List[str], index: int, is_ordered: bool) -> Tuple[Node, int]:
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
            match = re.match(r'^\d+\.\s(.*)$', line)
            if not match:
                return list_item(""), 1
            content = match.group(1)
        else:
            # Remove bullet prefix ("- " or "・")
            if line.startswith('- '):
                content = line[2:]
            elif line.startswith('・'):
                content = line[1:]
            else:
                content = line
        
        # Check for keyword syntax in list item
        if content.startswith(';;;') and ';;; ' in content:
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
        parts = content.split(';;; ', 1)
        if len(parts) != 2:
            return list_item(content)  # Fallback to regular item
        
        keyword_part = parts[0][3:]  # Remove leading ;;;
        text_content = parts[1]
        
        # Parse keywords
        keywords, attributes, errors = self.keyword_parser.parse_marker_keywords(keyword_part)
        
        if errors or not keywords:
            # If there are errors, create regular list item with error indication
            error_content = f"[ERROR: {'; '.join(errors)}] {text_content}" if errors else text_content
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
        
        if line.startswith('- ') or line.startswith('・'):
            return 'ul'
        elif re.match(r'^\d+\.\s', line):
            return 'ol'
        else:
            return ''
    
    def contains_list(self, content: str) -> bool:
        """
        Check if content contains list syntax
        
        Args:
            content: Content to check
        
        Returns:
            bool: True if content contains list syntax
        """
        lines = content.split('\n')
        for line in lines:
            if self.is_list_line(line):
                return True
        return False
    
    def extract_list_items(self, content: str) -> List[str]:
        """
        Extract list items from content
        
        Args:
            content: Content containing lists
        
        Returns:
            List[str]: List of item contents
        """
        items = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('- '):
                items.append(line[2:])
            elif line.startswith('・'):
                items.append(line[1:])
            elif re.match(r'^\d+\.\s', line):
                match = re.match(r'^\d+\.\s(.*)$', line)
                if match:
                    items.append(match.group(1))
        
        return items


class NestedListParser:
    """Parser for nested list structures"""
    
    def __init__(self, list_parser: ListParser):
        self.list_parser = list_parser
    
    def parse_nested_lists(self, lines: List[str], start_index: int) -> Tuple[Node, int]:
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
        
        if list_type == 'ul':
            return self.list_parser.parse_unordered_list(lines, start_index)
        elif list_type == 'ol':
            return self.list_parser.parse_ordered_list(lines, start_index)
        else:
            # Not a list
            return None, start_index
    
    def _calculate_indent_level(self, line: str) -> int:
        """Calculate indentation level of a line"""
        return len(line) - len(line.lstrip())
    
    def _group_by_indent_level(self, lines: List[str]) -> Dict[int, List[Tuple[int, str]]]:
        """Group list items by their indentation level"""
        groups = {}
        for i, line in enumerate(lines):
            if self.list_parser.is_list_line(line):
                indent = self._calculate_indent_level(line)
                if indent not in groups:
                    groups[indent] = []
                groups[indent].append((i, line))
        return groups


class ListValidator:
    """Validator for list syntax and structure"""
    
    def __init__(self, list_parser: ListParser):
        self.list_parser = list_parser
    
    def validate_list_structure(self, lines: List[str]) -> List[str]:
        """
        Validate list structure and return any issues
        
        Args:
            lines: Lines to validate
        
        Returns:
            List[str]: List of validation issues
        """
        issues = []
        current_list_type = None
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if not line_stripped:
                current_list_type = None
                continue
            
            list_type = self.list_parser.is_list_line(line_stripped)
            
            if list_type:
                # Check for list type consistency
                if current_list_type and current_list_type != list_type:
                    issues.append(f"行 {i+1}: リストタイプが混在しています ({current_list_type} → {list_type})")
                
                current_list_type = list_type
                
                # Validate keyword syntax in list items
                if list_type == 'ul' and ';;;' in line_stripped:
                    keyword_issues = self._validate_keyword_list_item(line_stripped, i+1)
                    issues.extend(keyword_issues)
            else:
                current_list_type = None
        
        return issues
    
    def _validate_keyword_list_item(self, line: str, line_number: int) -> List[str]:
        """Validate keyword syntax in a list item"""
        issues = []
        
        # Extract content after "- " or "・"
        if line.startswith('- '):
            content = line[2:]
        elif line.startswith('・'):
            content = line[1:]
        else:
            return issues
        
        # Check keyword format
        if content.startswith(';;;'):
            if ';;; ' not in content:
                issues.append(f"行 {line_number}: キーワードリスト項目の構文が不正です")
            else:
                # Extract and validate keyword
                parts = content.split(';;; ', 1)
                if len(parts) == 2:
                    keyword_part = parts[0][3:]  # Remove ;;;
                    keywords, _, errors = self.list_parser.keyword_parser.parse_marker_keywords(keyword_part)
                    
                    for error in errors:
                        issues.append(f"行 {line_number}: {error}")
                    
                    valid_keywords, validation_errors = self.list_parser.keyword_parser.validate_keywords(keywords)
                    for error in validation_errors:
                        issues.append(f"行 {line_number}: {error}")
        
        return issues