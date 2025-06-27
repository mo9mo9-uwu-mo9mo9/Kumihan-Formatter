"""Keyword parsing utilities for Kumihan-Formatter

This module handles the parsing and validation of Kumihan syntax keywords,
including compound keywords and error suggestions.
"""

import re
from typing import List, Dict, Tuple, Optional, Any
from difflib import get_close_matches

from .ast_nodes import Node, NodeBuilder, error_node


class KeywordParser:
    """Parser for Kumihan syntax keywords"""
    
    # Default block keyword definitions
    DEFAULT_BLOCK_KEYWORDS = {
        "太字": {"tag": "strong"},
        "イタリック": {"tag": "em"},
        "枠線": {"tag": "div", "class": "box"},
        "ハイライト": {"tag": "div", "class": "highlight"},
        "見出し1": {"tag": "h1"},
        "見出し2": {"tag": "h2"},
        "見出し3": {"tag": "h3"},
        "見出し4": {"tag": "h4"},
        "見出し5": {"tag": "h5"},
        "折りたたみ": {"tag": "details", "summary": "詳細を表示"},
        "ネタバレ": {"tag": "details", "summary": "ネタバレを表示"},
        "コードブロック": {"tag": "pre", "class": "code-block"},
        "コード": {"tag": "code", "class": "inline-code"},
    }
    
    # Keyword nesting order (outer to inner)
    NESTING_ORDER = [
        'details',  # 折りたたみ, ネタバレ
        'div',      # 枠線, ハイライト
        'h1', 'h2', 'h3', 'h4', 'h5',  # 見出し
        'strong',   # 太字
        'em'        # イタリック
    ]
    
    def __init__(self, config=None):
        """Initialize keyword parser with fixed keywords"""
        # 簡素化: 固定マーカーセットのみ使用
        self.BLOCK_KEYWORDS = self.DEFAULT_BLOCK_KEYWORDS.copy()
    
    def _normalize_marker_syntax(self, marker_content: str) -> str:
        """
        Normalize marker syntax for user-friendly input
        
        Accepts:
        - Full-width spaces (　) -> half-width spaces ( )
        - No space before attributes -> add space
        - Multiple spaces -> single space
        
        Args:
            marker_content: Raw marker content
        
        Returns:
            str: Normalized marker content
        """
        # Replace full-width spaces with half-width spaces
        normalized = marker_content.replace('　', ' ')
        
        # Add space before color= if missing
        normalized = re.sub(r'([^\s])color=', r'\1 color=', normalized)
        
        # Add space before alt= if missing  
        normalized = re.sub(r'([^\s])alt=', r'\1 alt=', normalized)
        
        # Normalize multiple spaces to single space
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Clean up leading/trailing spaces
        normalized = normalized.strip()
        
        return normalized
    
    def parse_marker_keywords(self, marker_content: str) -> Tuple[List[str], Dict[str, Any], List[str]]:
        """
        Parse keywords and attributes from marker content
        
        Args:
            marker_content: Content between ;;; markers
        
        Returns:
            tuple: (keywords, attributes, errors)
        """
        # Normalize marker content for user-friendly input
        marker_content = self._normalize_marker_syntax(marker_content)
        
        keywords = []
        attributes = {}
        errors = []
        
        # Extract color attribute
        color_match = re.search(r'color=([#\w]+)', marker_content)
        if color_match:
            attributes['color'] = color_match.group(1)
            marker_content = re.sub(r'\s*color=[#\w]+', '', marker_content)
        
        # Extract alt attribute (for images)
        alt_match = re.search(r'alt=([^;]+)', marker_content)
        if alt_match:
            attributes['alt'] = alt_match.group(1).strip()
            marker_content = re.sub(r'\s*alt=[^;]+', '', marker_content)
        
        # Split keywords by + or ＋
        if '+' in marker_content or '＋' in marker_content:
            # Compound keywords
            parts = re.split(r'[+＋]', marker_content)
            for part in parts:
                part = part.strip()
                if part:
                    keywords.append(part)
        else:
            # Single keyword
            keyword = marker_content.strip()
            if keyword:
                keywords.append(keyword)
        
        return keywords, attributes, errors
    
    def validate_keywords(self, keywords: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate keywords and return valid ones with errors
        
        Args:
            keywords: List of keywords to validate
        
        Returns:
            tuple: (valid_keywords, error_messages)
        """
        valid_keywords = []
        error_messages = []
        
        for keyword in keywords:
            if keyword in self.BLOCK_KEYWORDS:
                valid_keywords.append(keyword)
            else:
                error_msg = f"不明なキーワード: {keyword}"
                suggestions = self._get_keyword_suggestions(keyword)
                if suggestions:
                    error_msg += f" (候補: {', '.join(suggestions)})"
                error_messages.append(error_msg)
        
        return valid_keywords, error_messages
    
    def create_single_block(self, keyword: str, content: str, attributes: Dict[str, Any]) -> Node:
        """
        Create a single block node from keyword
        
        Args:
            keyword: Block keyword
            content: Block content
            attributes: Additional attributes
        
        Returns:
            Node: Created block node
        """
        if keyword not in self.BLOCK_KEYWORDS:
            return error_node(f"不明なキーワード: {keyword}")
        
        block_def = self.BLOCK_KEYWORDS[keyword]
        tag = block_def["tag"]
        
        # Parse content - for single blocks, use content directly if provided
        if content.strip():
            parsed_content = self._parse_block_content(content)
        else:
            parsed_content = [""]
        
        # Create node with appropriate builder
        builder = NodeBuilder(tag).content(parsed_content)
        
        # Add class if specified
        if "class" in block_def:
            builder.css_class(block_def["class"])
        
        # Add summary for details elements
        if "summary" in block_def:
            builder.attribute("summary", block_def["summary"])
        
        # Handle color attribute for highlight
        if keyword == "ハイライト" and "color" in attributes:
            color = attributes["color"]
            if not color.startswith('#'):
                color = '#' + color
            builder.style(f"background-color:{color}")
        
        # Add other attributes
        for key, value in attributes.items():
            if key not in ['color']:  # Skip already handled attributes
                builder.attribute(key, value)
        
        return builder.build()
    
    def create_compound_block(self, keywords: List[str], content: str, 
                            attributes: Dict[str, Any]) -> Node:
        """
        Create compound block node with nested keywords
        
        Args:
            keywords: List of keywords to apply
            content: Block content
            attributes: Additional attributes
        
        Returns:
            Node: Created compound block node
        """
        if not keywords:
            return error_node("空のキーワードリスト")
        
        # Validate all keywords first
        valid_keywords, error_messages = self.validate_keywords(keywords)
        
        if error_messages:
            return error_node("; ".join(error_messages))
        
        if not valid_keywords:
            return error_node("有効なキーワードがありません")
        
        # Sort keywords by nesting order (outer to inner)
        sorted_keywords = self._sort_keywords_by_nesting_order(valid_keywords)
        
        # Parse content
        parsed_content = self._parse_block_content(content)
        
        # Build nested structure from inner to outer
        current_content = parsed_content
        
        # Apply keywords from innermost to outermost
        for keyword in reversed(sorted_keywords):
            block_def = self.BLOCK_KEYWORDS[keyword]
            tag = block_def["tag"]
            
            # Create node with appropriate builder
            builder = NodeBuilder(tag).content(current_content)
            
            # Add class if specified
            if "class" in block_def:
                builder.css_class(block_def["class"])
            
            # Add summary for details elements
            if "summary" in block_def:
                builder.attribute("summary", block_def["summary"])
            
            # Handle color attribute for highlight
            if keyword == "ハイライト" and "color" in attributes:
                color = attributes["color"]
                if not color.startswith('#'):
                    color = '#' + color
                builder.style(f"background-color:{color}")
            
            # Create the node and make it the new current content
            current_node = builder.build()
            current_content = [current_node]
        
        # Return the outermost node
        return current_content[0] if isinstance(current_content, list) else current_content
    
    def _parse_block_content(self, content: str) -> List:
        """Parse block content into appropriate structure"""
        if not content.strip():
            return [""]
        
        # Process inline keyword markup in list items
        processed_content = self._process_inline_keywords(content)
        
        # Return content as text, not as paragraph node
        # The rendering will be handled by the specific keyword handler
        return [processed_content.strip()]
    
    def _process_inline_keywords(self, content: str) -> str:
        """Process inline keyword markup (e.g., ;;;keyword;;; text) in content"""
        import re
        
        # Pattern to match ;;;keyword;;; text at the start of lines or after list markers
        pattern = r'(^|\n)([\s]*[-*]?\s*)(;;;([^;]+);;;\s+)(.+?)(?=\n|$)'
        
        def replace_keyword(match):
            prefix = match.group(1)  # \n or start
            list_marker = match.group(2)  # list marker and spaces
            full_marker = match.group(3)  # ;;;keyword;;; 
            keyword_part = match.group(4)  # keyword content
            text_content = match.group(5)  # text after keyword
            
            # Parse keywords
            keywords, attributes, errors = self.parse_marker_keywords(keyword_part)
            
            if errors or not keywords:
                # If there are errors, return original text
                return prefix + list_marker + full_marker + text_content
            
            # Apply styling to text content
            if len(keywords) == 1:
                # Single keyword - apply simple styling
                styled_text = self._apply_simple_styling(keywords[0], text_content, attributes)
            else:
                # Multiple keywords - apply compound styling  
                styled_text = self._apply_compound_styling(keywords, text_content, attributes)
            
            return prefix + list_marker + styled_text
        
        return re.sub(pattern, replace_keyword, content, flags=re.MULTILINE)
    
    def _apply_simple_styling(self, keyword: str, text: str, attributes: dict) -> str:
        """Apply simple styling to text based on keyword"""
        if keyword == "太字":
            return f"<strong>{text}</strong>"
        elif keyword == "イタリック":
            return f"<em>{text}</em>"
        elif keyword == "ハイライト":
            style = ""
            if "color" in attributes:
                color = attributes["color"]
                if not color.startswith('#'):
                    color = '#' + color
                style = f' style="background-color:{color}"'
            return f'<span class="highlight"{style}>{text}</span>'
        elif keyword == "枠線":
            return f'<span class="box-inline">{text}</span>'
        elif keyword.startswith("見出し"):
            level = keyword[-1]
            return f'<span class="heading-{level}">{text}</span>'
        else:
            return text
    
    def _apply_compound_styling(self, keywords: List[str], text: str, attributes: dict) -> str:
        """Apply compound styling to text"""
        # Sort keywords by nesting order
        sorted_keywords = self._sort_keywords_by_nesting_order(keywords)
        
        # Apply styling from inner to outer
        result = text
        for keyword in reversed(sorted_keywords):
            result = self._apply_simple_styling(keyword, result, attributes)
        
        return result
    
    def _sort_keywords_by_nesting_order(self, keywords: List[str]) -> List[str]:
        """Sort keywords by their nesting order"""
        def get_tag_priority(keyword: str) -> int:
            if keyword not in self.BLOCK_KEYWORDS:
                return 999
            
            tag = self.BLOCK_KEYWORDS[keyword]["tag"]
            try:
                return self.NESTING_ORDER.index(tag)
            except ValueError:
                return 999
        
        return sorted(keywords, key=get_tag_priority)
    
    def _find_node_by_keyword(self, node: Node, keyword: str) -> Optional[Node]:
        """Find a node created by a specific keyword"""
        if keyword not in self.BLOCK_KEYWORDS:
            return None
        
        target_tag = self.BLOCK_KEYWORDS[keyword]["tag"]
        target_class = self.BLOCK_KEYWORDS[keyword].get("class")
        
        # Check current node
        if node.type == target_tag:
            if target_class is None or node.get_attribute('class') == target_class:
                return node
        
        # Search recursively
        if isinstance(node.content, list):
            for item in node.content:
                if isinstance(item, Node):
                    result = self._find_node_by_keyword(item, keyword)
                    if result:
                        return result
        
        return None
    
    def _get_keyword_suggestions(self, invalid_keyword: str, max_suggestions: int = 3) -> List[str]:
        """Get suggestions for invalid keywords"""
        all_keywords = list(self.BLOCK_KEYWORDS.keys())
        suggestions = get_close_matches(
            invalid_keyword, 
            all_keywords, 
            n=max_suggestions, 
            cutoff=0.6
        )
        return suggestions
    
    def get_all_keywords(self) -> List[str]:
        """Get list of all available keywords"""
        return list(self.BLOCK_KEYWORDS.keys())
    
    def is_valid_keyword(self, keyword: str) -> bool:
        """Check if a keyword is valid"""
        return keyword in self.BLOCK_KEYWORDS
    
    def get_keyword_info(self, keyword: str) -> Optional[Dict[str, Any]]:
        """Get information about a keyword"""
        return self.BLOCK_KEYWORDS.get(keyword)
    
    def add_custom_keyword(self, keyword: str, definition: Dict[str, Any]) -> None:
        """Add a custom keyword definition"""
        self.BLOCK_KEYWORDS[keyword] = definition
    
    def remove_keyword(self, keyword: str) -> bool:
        """Remove a keyword definition"""
        if keyword in self.BLOCK_KEYWORDS:
            del self.BLOCK_KEYWORDS[keyword]
            return True
        return False


class MarkerValidator:
    """Validator for marker syntax and structure"""
    
    def __init__(self, keyword_parser: KeywordParser):
        self.keyword_parser = keyword_parser
    
    def validate_marker_line(self, line: str) -> Tuple[bool, List[str]]:
        """
        Validate a complete marker line
        
        Args:
            line: Line to validate
        
        Returns:
            tuple: (is_valid, error_messages)
        """
        errors = []
        
        # Check basic marker format
        if not line.strip().startswith(';;;'):
            errors.append("マーカーは ;;; で開始する必要があります")
            return False, errors
        
        # Extract marker content (opening marker format: ;;;keyword)
        marker_content = line.strip()[3:].strip()
        
        if not marker_content:
            errors.append("空のマーカーです")
            return False, errors
        
        # Parse keywords
        keywords, attributes, parse_errors = self.keyword_parser.parse_marker_keywords(marker_content)
        errors.extend(parse_errors)
        
        # Validate keywords
        valid_keywords, validation_errors = self.keyword_parser.validate_keywords(keywords)
        errors.extend(validation_errors)
        
        return len(errors) == 0, errors
    
    def validate_block_structure(self, lines: List[str], start_index: int) -> Tuple[bool, Optional[int], List[str]]:
        """
        Validate block structure starting from a marker line
        
        Args:
            lines: All lines in the document
            start_index: Index of the opening marker
        
        Returns:
            tuple: (is_valid, end_index, error_messages)
        """
        errors = []
        
        if start_index >= len(lines):
            errors.append("開始マーカーのインデックスが範囲外です")
            return False, None, errors
        
        # Find closing marker
        for i in range(start_index + 1, len(lines)):
            line = lines[i].strip()
            if line == ';;;':
                return True, i, errors
        
        errors.append(f"行 {start_index + 1}: 閉じマーカー ;;; が見つかりません")
        return False, None, errors