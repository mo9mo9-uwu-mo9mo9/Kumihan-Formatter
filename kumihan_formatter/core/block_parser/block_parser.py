"""Block parsing utilities for Kumihan-Formatter

This module handles the parsing of basic block-level elements.
新記法 #キーワード# 対応 - Issue #665
"""

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from ..ast_nodes import Node
from ..keyword_parser import KeywordParser

if TYPE_CHECKING:
    pass


class BlockParser:
    """Main block parser that integrates specialized parsers.

    This class maintains API compatibility while delegating functionality
    to specialized parser components for better maintainability.

    Refactored: 2025-08-10 (Error問題修正 - 711行から軽量化)
    """

    def __init__(self, keyword_parser: Optional["KeywordParser"] = None) -> None:
        """Initialize block parser with specialized components.

        Args:
            keyword_parser: Optional keyword parser instance
        """
        from kumihan_formatter.core.utilities.logger import get_logger

        from .base_parser import BaseBlockParser
        from .content_parser import ContentParser
        from .marker_parser import MarkerBlockParser
        from .text_parser import TextBlockParser

        self.logger = get_logger(__name__)
        self.keyword_parser = keyword_parser
        self.heading_counter = 0

        # Initialize specialized parsers
        self.base_parser = BaseBlockParser(keyword_parser)
        self.text_parser = TextBlockParser(keyword_parser)
        self.marker_parser = MarkerBlockParser(keyword_parser)
        self.content_parser = ContentParser(keyword_parser)

        # Set parser references for inter-component communication
        self._setup_parser_references()

        # Legacy attributes for compatibility
        self._block_end_indices: Dict[int, int] = {}
        self._lines_cache: List[str] = []
        self._list_pattern = re.compile(r"^\s*[*+-]\s+|^\s*\d+\.\s+")
        self._empty_line_pattern = re.compile(r"^\s*$")
        self._is_marker_cache: Dict[str, bool] = {}
        self._is_list_cache: Dict[str, bool] = {}
        self.parser_ref = None

    def _setup_parser_references(self) -> None:
        """Setup cross-references between parser components."""
        self.base_parser.set_parser_reference(self)
        self.text_parser.set_parser_reference(self)
        self.marker_parser.set_parser_reference(self)
        self.content_parser.set_parser_reference(self)

    def set_parser_reference(self, parser: Any) -> None:
        """Set reference to main parser for recursive calls.

        Args:
            parser: Main parser instance for recursive calls
        """
        self.parser_ref = parser
        # Propagate to specialized parsers
        self.base_parser.set_parser_reference(parser)
        self.text_parser.set_parser_reference(parser)
        self.marker_parser.set_parser_reference(parser)
        self.content_parser.set_parser_reference(parser)

    # === Core parsing methods (delegation to specialized parsers) ===

    def parse_block_marker(
        self, lines: List[str], start_index: int
    ) -> Tuple["Node", int]:
        """Parse block marker (delegates to marker parser).

        Args:
            lines: List of input lines
            start_index: Starting index for parsing

        Returns:
            Tuple of (parsed node, next index)
        """
        return self.marker_parser.parse_block_marker(lines, start_index)

    def parse_new_format_marker(
        self, lines: List[str], start_index: int
    ) -> Tuple["Node", int]:
        """Parse new format marker (delegates to marker parser).

        Args:
            lines: List of input lines
            start_index: Starting index for parsing

        Returns:
            Tuple of (parsed node, next index)
        """
        return self.marker_parser.parse_new_format_marker(lines, start_index)

    def parse_paragraph(self, lines: List[str], start_index: int) -> Tuple["Node", int]:
        """Parse paragraph (delegates to text parser).

        Args:
            lines: List of input lines
            start_index: Starting index for parsing

        Returns:
            Tuple of (parsed paragraph node, next index)
        """
        return self.text_parser.parse_paragraph(lines, start_index)

    def is_block_marker_line(self, line: str) -> bool:
        """Check if line is a block marker line."""
        return self.base_parser.is_block_marker_line(line)

    def is_opening_marker(self, line: str) -> bool:
        """Check if line is an opening marker."""
        return self.base_parser.is_opening_marker(line)

    def is_closing_marker(self, line: str) -> bool:
        """Check if line is a closing marker."""
        return self.base_parser.is_closing_marker(line)

    def skip_empty_lines(self, lines: List[str], start_index: int) -> int:
        """Skip empty lines and return next non-empty index."""
        return self.base_parser.skip_empty_lines(lines, start_index)

    def find_next_significant_line(self, lines: List[str], start_index: int) -> int:
        """Find next significant (non-empty, non-comment) line."""
        return self.base_parser.find_next_significant_line(lines, start_index)

    def _is_marker_internal(self, line: str) -> bool:
        """Internal marker detection."""
        return self.base_parser._is_marker_internal(line)

    def _is_list_internal(self, line: str) -> bool:
        """Internal list detection."""
        return self.base_parser._is_list_internal(line)

    def _preprocess_lines(self, lines: List[str]) -> List[str]:
        """Preprocess lines for parsing optimization."""
        return self.base_parser._preprocess_lines(lines)

    def _find_next_block_end(self, start_index: int) -> int:
        """Find the end index of the next block with caching."""
        return self.base_parser._find_next_block_end(start_index)

    def _is_block_marker_cached(
        self, line: str, keyword_parser: Optional["KeywordParser"] = None
    ) -> bool:
        """Check if line is block marker with caching."""
        return self.base_parser._is_block_marker_cached(line, keyword_parser)

    def _parse_inline_format(
        self,
        keywords: List[str],
        attributes: Dict[str, Any],
        content: str,
        start_index: int,
    ) -> Tuple["Node", int]:
        """Parse inline format marker."""
        return self.marker_parser._parse_inline_format(
            keywords, attributes, content, start_index
        )

    def _create_node_for_keyword(self, keyword: str, content: str) -> Optional["Node"]:
        """Create appropriate node for given keyword and content."""
        return self.content_parser._create_node_for_keyword(keyword, content)

    def _apply_attributes_to_node(
        self, node: "Node", attributes: Dict[str, Any]
    ) -> None:
        """Apply attributes to node."""
        return self.content_parser._apply_attributes_to_node(node, attributes)

    def _parse_new_format_block(
        self,
        lines: List[str],
        start_index: int,
        keywords: List[str],
        attributes: Dict[str, Any],
    ) -> Tuple["Node", int]:
        """Parse new format block content."""
        return self.content_parser._parse_new_format_block(
            lines, start_index, keywords, attributes
        )

    def _generate_block_fix_suggestions(
        self, opening_line: str, keywords: List[str]
    ) -> str:
        """Generate fix suggestions for malformed blocks."""
        return self.content_parser._generate_block_fix_suggestions(
            opening_line, keywords
        )

    def _attempt_content_recovery(self, lines: List[str], start_index: int) -> str:
        """Attempt to recover content from malformed block."""
        return self.content_parser._attempt_content_recovery(lines, start_index)

    def _parse_list_block(
        self,
        lines: List[str],
        start_index: int,
        keywords: List[str],
        attributes: Dict[str, Any],
    ) -> Tuple["Node", int]:
        """Parse list block using list parser."""
        return self.content_parser._parse_list_block(
            lines, start_index, keywords, attributes
        )

    def _is_simple_image_marker(self, line: str) -> bool:
        """Check if line is a simple image marker."""
        return self.marker_parser._is_simple_image_marker(line)

    def _is_comment_line(self, line: str) -> bool:
        """Check if line is a comment line."""
        return self.base_parser._is_comment_line(line)
