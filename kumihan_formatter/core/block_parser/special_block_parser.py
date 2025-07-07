"""Special block parsing utilities for Kumihan-Formatter

This module handles parsing of special block types including code blocks,
tables, and other special formatting elements.
"""

from typing import Any

from ..ast_nodes import Node, NodeBuilder, error_node, paragraph


class SpecialBlockParser:
    """Parser for special block types"""

    def __init__(self, block_parser: Any) -> None:
        self.block_parser = block_parser

    def parse_code_block(self, lines: list[str], start_index: int) -> tuple[Node, int]:
        """Parse a code block"""
        # Find closing marker
        end_index = None
        for i in range(start_index + 1, len(lines)):
            if lines[i].strip() == ";;;":
                end_index = i
                break

        if end_index is None:
            return (
                error_node("コードブロックの閉じマーカーが見つかりません"),
                start_index + 1,
            )

        # Extract code content
        code_lines = lines[start_index + 1 : end_index]
        code_content = "\n".join(code_lines)

        # Create code block node
        builder = NodeBuilder("pre").content(code_content)

        return builder.build(), end_index + 1

    def parse_details_block(self, summary_text: str, content: str) -> Node:
        """Parse a details/summary block"""
        builder = NodeBuilder("details")
        builder.attribute("summary", summary_text)

        # Parse content
        content_node = paragraph(content) if content.strip() else paragraph("")
        builder.content([content_node])

        return builder.build()

    def parse_table_block(self, lines: list[str], start_index: int) -> tuple[Node, int]:
        """Parse a table block (future enhancement)"""
        # TODO: Implement table parsing
        return error_node("テーブル機能は未実装です"), start_index + 1
