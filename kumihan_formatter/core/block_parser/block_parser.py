"""Block parsing utilities for Kumihan-Formatter

This module handles the parsing of basic block-level elements.
"""

import re
from typing import List, Optional, Tuple

from ..ast_nodes import Node, error_node, paragraph, toc_marker
from ..keyword_parser import KeywordParser, MarkerValidator


class BlockParser:
    """Parser for block-level elements"""

    def __init__(self, keyword_parser: KeywordParser):
        self.keyword_parser = keyword_parser
        self.marker_validator = MarkerValidator(keyword_parser)
        self.heading_counter = 0

    def parse_block_marker(
        self, lines: List[str], start_index: int
    ) -> Tuple[Optional[Node], int]:
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

        # Handle image markers - delegate to image parser
        if (
            marker_content.startswith("画像")
            or ";;;画像" in opening_line
            or self._is_simple_image_marker(opening_line)
        ):
            # Import here to avoid circular imports
            from .image_block_parser import ImageBlockParser

            image_parser = ImageBlockParser(self)
            return image_parser.parse_image_block(lines, start_index)

        # Find closing marker
        (
            is_valid,
            end_index,
            validation_errors,
        ) = self.marker_validator.validate_block_structure(lines, start_index)

        if not is_valid:
            return (
                error_node("; ".join(validation_errors), start_index + 1),
                start_index + 1,
            )

        # Extract content between markers
        content_lines = lines[start_index + 1 : end_index]
        content = "\n".join(content_lines).strip()

        # Handle empty marker (;;; with no keywords)
        if not marker_content:
            return paragraph(content), end_index + 1

        # Parse keywords and attributes
        keywords, attributes, parse_errors = self.keyword_parser.parse_marker_keywords(
            marker_content
        )

        if parse_errors:
            return error_node("; ".join(parse_errors), start_index + 1), end_index + 1

        # Create block node
        if len(keywords) == 1:
            node = self.keyword_parser.create_single_block(
                keywords[0], content, attributes
            )
        else:
            node = self.keyword_parser.create_compound_block(
                keywords, content, attributes
            )

        # Add heading ID if this is a heading
        if any(keyword.startswith("見出し") for keyword in keywords):
            self.heading_counter += 1
            if hasattr(node, "add_attribute"):
                node.add_attribute("id", f"heading-{self.heading_counter}")

        return node, end_index + 1

    def _is_simple_image_marker(self, line: str) -> bool:
        """
        Check if a line is a simple image marker (;;;filename.ext;;;)
        """
        line = line.strip()
        if not (
            line.startswith(";;;") and line.endswith(";;;") and line.count(";;;") >= 2
        ):
            return False

        parts = line.split(";;;")
        if len(parts) < 3:
            return False

        filename = parts[1].strip()
        if not filename:
            return False

        # Check for common image extensions
        image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]
        return any(filename.lower().endswith(ext) for ext in image_extensions)

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
            if line.startswith("- ") or re.match(r"^\d+\.\s", line):
                break

            # Stop at block markers
            if line.startswith(";;;"):
                break

            paragraph_lines.append(line)
            current_index += 1

        if not paragraph_lines:
            return None, start_index

        # Join lines with space
        content = " ".join(paragraph_lines)

        return paragraph(content), current_index

    def is_block_marker_line(self, line: str) -> bool:
        """Check if a line is a block marker"""
        line = line.strip()
        return line.startswith(";;;") and (line.endswith(";;;") or line == ";;;")

    def is_opening_marker(self, line: str) -> bool:
        """Check if a line is an opening block marker"""
        line = line.strip()
        # Opening marker: ;;;keyword but NOT just ;;;
        # ;;; alone is always a closing marker
        # Also not ;;;something;;; (single-line markers)
        return (
            line.startswith(";;;")
            and line != ";;;"
            and not (line.endswith(";;;") and line.count(";;;") > 1)
        )

    def is_closing_marker(self, line: str) -> bool:
        """Check if a line is a closing block marker"""
        return line.strip() == ";;;"

    def skip_empty_lines(self, lines: List[str], start_index: int) -> int:
        """Skip empty lines and return the next non-empty line index"""
        index = start_index
        while index < len(lines) and not lines[index].strip():
            index += 1
        return index

    def find_next_significant_line(
        self, lines: List[str], start_index: int
    ) -> Optional[int]:
        """Find the next line that contains significant content"""
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            if line and not self._is_comment_line(line):
                return i
        return None

    def _is_comment_line(self, line: str) -> bool:
        """Check if a line is a comment (starts with #)"""
        return line.strip().startswith("#")
