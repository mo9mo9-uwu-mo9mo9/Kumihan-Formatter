"""Image block parsing utilities for Kumihan-Formatter

This module handles parsing of image blocks and image-related elements.
"""

from typing import Any

from ...ast_nodes import Node


class ImageBlockParser:
    """Parser for image blocks"""

    def __init__(self, block_parser: Any) -> None:
        self.block_parser = block_parser

    def parse_image_block(self, lines: list[str], start_index: int) -> tuple[Node, int]:
        """
        Parse an image block

        ;;;記法は削除されました（Phase 1）
        この機能は新記法で置き換えられます
        """
        from kumihan_formatter.core.ast_nodes.factories import error_node

        return (
            error_node(";;;記法は削除されました（Phase 1）", start_index + 1),
            start_index + 1,
        )
