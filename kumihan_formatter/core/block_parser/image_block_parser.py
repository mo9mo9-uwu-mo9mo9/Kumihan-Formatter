"""Image block parsing utilities for Kumihan-Formatter

This module handles parsing of image blocks and image-related elements.
"""

import re
from typing import List, Tuple

from ..ast_nodes import Node, error_node, image_node


class ImageBlockParser:
    """Parser for image blocks"""

    def __init__(self, block_parser):
        self.block_parser = block_parser

    def parse_image_block(self, lines: List[str], start_index: int) -> Tuple[Node, int]:
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
        if opening_line.count(";;;") >= 2 and not opening_line.endswith(";;;画像"):
            # Extract filename from single line
            parts = opening_line.split(";;;")
            if len(parts) >= 3:
                filename = parts[1].strip()

                # Extract alt text if present
                alt_text = None
                if "alt=" in opening_line:
                    alt_match = re.search(r"alt=([^;]+)", opening_line)
                    if alt_match:
                        alt_text = alt_match.group(1).strip()

                return image_node(filename, alt_text), start_index + 1

        # Handle multi-line image block
        marker_content = opening_line[3:].strip()

        # Find closing marker
        end_index = None
        for i in range(start_index + 1, len(lines)):
            if lines[i].strip() == ";;;":
                end_index = i
                break

        if end_index is None:
            return (
                error_node(
                    "画像ブロックの閉じマーカーが見つかりません", start_index + 1
                ),
                start_index + 1,
            )

        # Extract filename from content
        content_lines = lines[start_index + 1 : end_index]
        content = "\n".join(content_lines).strip()

        if not content:
            return (
                error_node("画像ファイル名が指定されていません", start_index + 1),
                end_index + 1,
            )

        # Extract alt text from marker
        alt_text = None
        if "alt=" in marker_content:
            alt_match = re.search(r"alt=([^;]+)", marker_content)
            if alt_match:
                alt_text = alt_match.group(1).strip()

        # Use first line as filename
        filename = content_lines[0].strip() if content_lines else content

        return image_node(filename, alt_text), end_index + 1
