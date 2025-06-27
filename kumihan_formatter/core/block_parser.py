"""Block parsing utilities for Kumihan-Formatter

This module handles the parsing of block-level elements including
paragraphs, block markers, and special blocks.
"""

import re
from typing import List, Optional, Tuple, Dict, Any

from .ast_nodes import Node, NodeBuilder, paragraph, error_node, toc_marker, image_node
from .keyword_parser import KeywordParser, MarkerValidator


class BlockParser:
    """Parser for block-level elements"""
    
    def __init__(self, keyword_parser: KeywordParser):
        self.keyword_parser = keyword_parser
        self.marker_validator = MarkerValidator(keyword_parser)
        self.heading_counter = 0
    
    def parse_block_marker(self, lines: List[str], start_index: int) -> Tuple[Optional[Node], int]:
        """
        Parse a block marker starting from the given index
        
        Args:
            lines: All lines in the document
            start_index: Index of the opening marker
        
        Returns:
            tuple: (parsed_node, next_index)
        """
        if start_index >= len(lines):
            return None, start_index
        
        opening_line = lines[start_index].strip()
        
        # Validate opening marker
        is_valid, errors = self.marker_validator.validate_marker_line(opening_line)
        if not is_valid:
            return error_node("; ".join(errors), start_index + 1), start_index + 1
        
        # Extract marker content
        marker_content = opening_line[3:].strip()
        
        # Handle special markers
        if marker_content == "目次":
            return toc_marker(), start_index + 1
        
        # Handle image markers
        if marker_content.startswith("画像") or ";;;画像" in opening_line:
            return self._parse_image_block(lines, start_index)
        
        # Find closing marker
        is_valid, end_index, validation_errors = self.marker_validator.validate_block_structure(
            lines, start_index
        )
        
        if not is_valid:
            return error_node("; ".join(validation_errors), start_index + 1), start_index + 1
        
        # Extract content between markers
        content_lines = lines[start_index + 1:end_index]
        content = '\n'.join(content_lines).strip()
        
        # Handle empty marker (;;; with no keywords)
        if not marker_content:
            # Create a simple paragraph node for empty markers
            from .ast_nodes import paragraph
            return paragraph(content), end_index + 1
        
        # Parse keywords and attributes
        keywords, attributes, parse_errors = self.keyword_parser.parse_marker_keywords(marker_content)
        
        if parse_errors:
            return error_node("; ".join(parse_errors), start_index + 1), end_index + 1
        
        # Create block node
        if len(keywords) == 1:
            node = self.keyword_parser.create_single_block(keywords[0], content, attributes)
        else:
            node = self.keyword_parser.create_compound_block(keywords, content, attributes)
        
        # Add heading ID if this is a heading
        if any(keyword.startswith('見出し') for keyword in keywords):
            self.heading_counter += 1
            if hasattr(node, 'add_attribute'):
                node.add_attribute('id', f'heading-{self.heading_counter}')
        
        return node, end_index + 1
    
    def _parse_image_block(self, lines: List[str], start_index: int) -> Tuple[Node, int]:
        """
        Parse an image block
        
        Args:
            lines: All lines in the document
            start_index: Index of the image marker line
        
        Returns:
            tuple: (image_node, next_index)
        """
        opening_line = lines[start_index].strip()
        
        # Handle single-line image marker: ;;;filename;;;
        if opening_line.count(';;;') >= 2 and not opening_line.endswith(';;;画像'):
            # Extract filename from single line
            parts = opening_line.split(';;;')
            if len(parts) >= 3:
                filename = parts[1].strip()
                
                # Extract alt text if present
                alt_text = None
                if 'alt=' in opening_line:
                    alt_match = re.search(r'alt=([^;]+)', opening_line)
                    if alt_match:
                        alt_text = alt_match.group(1).strip()
                
                return image_node(filename, alt_text), start_index + 1
        
        # Handle multi-line image block
        marker_content = opening_line[3:].strip()
        
        # Find closing marker
        end_index = None
        for i in range(start_index + 1, len(lines)):
            if lines[i].strip() == ';;;':
                end_index = i
                break
        
        if end_index is None:
            return error_node("画像ブロックの閉じマーカーが見つかりません", start_index + 1), start_index + 1
        
        # Extract filename from content
        content_lines = lines[start_index + 1:end_index]
        content = '\n'.join(content_lines).strip()
        
        if not content:
            return error_node("画像ファイル名が指定されていません", start_index + 1), end_index + 1
        
        # Extract alt text from marker
        alt_text = None
        if 'alt=' in marker_content:
            alt_match = re.search(r'alt=([^;]+)', marker_content)
            if alt_match:
                alt_text = alt_match.group(1).strip()
        
        # Use first line as filename
        filename = content_lines[0].strip() if content_lines else content
        
        return image_node(filename, alt_text), end_index + 1
    
    def parse_paragraph(self, lines: List[str], start_index: int) -> Tuple[Node, int]:
        """
        Parse a paragraph starting from the given index
        
        Args:
            lines: All lines in the document
            start_index: Index where paragraph starts
        
        Returns:
            tuple: (paragraph_node, next_index)
        """
        paragraph_lines = []
        current_index = start_index
        
        # Collect consecutive non-empty lines
        while current_index < len(lines):
            line = lines[current_index].strip()
            
            # Stop at empty lines
            if not line:
                break
            
            # Stop at list items
            if line.startswith('- ') or re.match(r'^\d+\.\s', line):
                break
            
            # Stop at block markers
            if line.startswith(';;;'):
                break
            
            paragraph_lines.append(line)
            current_index += 1
        
        if not paragraph_lines:
            return None, start_index
        
        # Join lines with space
        content = ' '.join(paragraph_lines)
        
        return paragraph(content), current_index
    
    def is_block_marker_line(self, line: str) -> bool:
        """Check if a line is a block marker"""
        line = line.strip()
        return line.startswith(';;;') and (line.endswith(';;;') or line == ';;;')
    
    def is_opening_marker(self, line: str) -> bool:
        """Check if a line is an opening block marker"""
        line = line.strip()
        # Opening marker: ;;;keyword OR just ;;; (for empty blocks)
        # But not ;;;something;;; (single-line markers)
        return (line.startswith(';;;') and 
                not (line.endswith(';;;') and line.count(';;;') > 1))
    
    def is_closing_marker(self, line: str) -> bool:
        """Check if a line is a closing block marker"""
        return line.strip() == ';;;'
    
    def skip_empty_lines(self, lines: List[str], start_index: int) -> int:
        """Skip empty lines and return the next non-empty line index"""
        index = start_index
        while index < len(lines) and not lines[index].strip():
            index += 1
        return index
    
    def find_next_significant_line(self, lines: List[str], start_index: int) -> Optional[int]:
        """Find the next line that contains significant content"""
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            if line and not self._is_comment_line(line):
                return i
        return None
    
    def _is_comment_line(self, line: str) -> bool:
        """Check if a line is a comment (starts with #)"""
        return line.strip().startswith('#')


class SpecialBlockParser:
    """Parser for special block types"""
    
    def __init__(self, block_parser: BlockParser):
        self.block_parser = block_parser
    
    def parse_code_block(self, lines: List[str], start_index: int) -> Tuple[Node, int]:
        """Parse a code block"""
        # Find closing marker
        end_index = None
        for i in range(start_index + 1, len(lines)):
            if lines[i].strip() == ';;;':
                end_index = i
                break
        
        if end_index is None:
            return error_node("コードブロックの閉じマーカーが見つかりません"), start_index + 1
        
        # Extract code content
        code_lines = lines[start_index + 1:end_index]
        code_content = '\n'.join(code_lines)
        
        # Create code block node
        builder = NodeBuilder('pre').css_class('code-block').content(code_content)
        
        return builder.build(), end_index + 1
    
    def parse_details_block(self, summary_text: str, content: str) -> Node:
        """Parse a details/summary block"""
        builder = NodeBuilder('details')
        builder.attribute('summary', summary_text)
        
        # Parse content
        content_node = paragraph(content) if content.strip() else paragraph("")
        builder.content([content_node])
        
        return builder.build()
    
    def parse_table_block(self, lines: List[str], start_index: int) -> Tuple[Node, int]:
        """Parse a table block (future enhancement)"""
        # TODO: Implement table parsing
        return error_node("テーブル機能は未実装です"), start_index + 1


class BlockValidator:
    """Validator for block structure and syntax"""
    
    def __init__(self, block_parser: BlockParser):
        self.block_parser = block_parser
    
    def validate_document_structure(self, lines: List[str]) -> List[str]:
        """
        Validate overall document structure
        
        Args:
            lines: Document lines to validate
        
        Returns:
            List[str]: List of validation issues
        """
        issues = []
        open_blocks = []
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            if self.block_parser.is_opening_marker(line_stripped):
                # Track opening markers
                open_blocks.append((i + 1, line_stripped))
            elif self.block_parser.is_closing_marker(line_stripped):
                # Check for matching opening marker
                if not open_blocks:
                    issues.append(f"行 {i+1}: 対応する開始マーカーのない閉じマーカー")
                else:
                    open_blocks.pop()
        
        # Check for unclosed blocks
        for line_num, marker in open_blocks:
            issues.append(f"行 {line_num}: 閉じマーカーのないブロック: {marker}")
        
        return issues
    
    def validate_block_nesting(self, lines: List[str]) -> List[str]:
        """Validate block nesting rules"""
        issues = []
        # TODO: Implement nesting validation
        return issues
    
    def validate_content_structure(self, content: str) -> List[str]:
        """Validate content within blocks"""
        issues = []
        
        # Check for invalid content patterns
        if ';;;' in content and not self._is_valid_nested_marker(content):
            issues.append("ブロック内での不正なマーカー使用")
        
        return issues
    
    def _is_valid_nested_marker(self, content: str) -> bool:
        """Check if nested markers are valid"""
        # TODO: Implement nested marker validation
        return True