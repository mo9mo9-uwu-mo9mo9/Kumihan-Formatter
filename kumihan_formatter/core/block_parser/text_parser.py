"""Text block parser for paragraph and text content processing.

Handles:
- Paragraph parsing
- Text content processing
- Content validation and normalization

Created: 2025-08-10 (Error問題修正 - BlockParser分割)
"""

from typing import TYPE_CHECKING, List, Optional, Tuple

from kumihan_formatter.core.ast_nodes import paragraph

from .base_parser import BaseBlockParser

if TYPE_CHECKING:
    from kumihan_formatter.core.ast_nodes import Node

    from ..keyword_parser import KeywordParser


class TextBlockParser(BaseBlockParser):
    """Specialized parser for text blocks and paragraphs."""

    def __init__(self, keyword_parser: Optional["KeywordParser"] = None) -> None:
        """Initialize text block parser.

        Args:
            keyword_parser: Optional keyword parser instance
        """
        super().__init__(keyword_parser)

    def parse_paragraph(self, lines: List[str], start_index: int) -> Tuple["Node", int]:
        """Parse paragraph content from lines.

        Args:
            lines: List of input lines
            start_index: Starting index for parsing

        Returns:
            Tuple of (parsed paragraph node, next index)
        """
        if start_index >= len(lines):
            from kumihan_formatter.core.ast_nodes import error_node

            return (
                error_node(
                    "段落解析エラー",
                    f"開始インデックス {start_index} が行数 {len(lines)} を超えています",
                    start_index,
                ),
                start_index + 1,
            )

        # Skip empty lines at start
        start_index = self.skip_empty_lines(lines, start_index)
        if start_index >= len(lines):
            from kumihan_formatter.core.ast_nodes import error_node

            return error_node(
                "段落解析エラー",
                "空行をスキップした後、処理する行が見つかりません",
                start_index,
            ), len(lines)

        # Collect paragraph lines
        paragraph_lines = []
        current_index = start_index

        while current_index < len(lines):
            line = lines[current_index]

            # Stop at empty line
            if not line.strip():
                break

            # Stop at block markers
            if self.is_block_marker_line(line):
                break

            paragraph_lines.append(line)
            current_index += 1

        # Process paragraph content
        content = "\n".join(paragraph_lines).strip()

        # Apply inline processing if parser reference available
        processed_content = content
        if self.parser_ref and hasattr(self.parser_ref, "inline_parser"):
            try:
                processed_content = self.parser_ref.inline_parser.process_text(content)
            except Exception as e:
                self.logger.warning(f"Inline processing failed: {e}")
                processed_content = content

        # Create paragraph node
        if processed_content:
            paragraph_node = paragraph(processed_content)
        else:
            from kumihan_formatter.core.ast_nodes import error_node

            paragraph_node = error_node("空段落エラー", "段落内容が空です", start_index)

        return paragraph_node, current_index

    def _normalize_text_content(self, content: str) -> str:
        """Normalize text content for consistent processing.

        Args:
            content: Raw text content

        Returns:
            Normalized text content
        """
        if not content:
            return ""

    def _validate_text_content(self, content: str) -> bool:
        """Validate text content.

        Args:
            content: Text content to validate

        Returns:
            True if content is valid
        """
        if not content or not content.strip():
            return False

    def _process_text_lines(self, lines: List[str]) -> str:
        """Process multiple text lines into single content.

        Args:
            lines: List of text lines

        Returns:
            Processed text content
        """
        if not lines:
            return ""
