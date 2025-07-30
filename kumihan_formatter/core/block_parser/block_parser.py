"""Block parsing utilities for Kumihan-Formatter

This module handles the parsing of basic block-level elements.
新記法 #キーワード# 対応 - Issue #665
"""

import re
from typing import Any

from ..ast_nodes import Node, error_node, paragraph, toc_marker
from ..keyword_parser import KeywordParser
from ..utilities.logger import get_logger


class BlockParser:
    """Parser for block-level elements"""

    def __init__(self, keyword_parser: KeywordParser):
        self.logger = get_logger(__name__)
        self.keyword_parser = keyword_parser
        self.heading_counter = 0
        self.logger.debug("BlockParser initialized")

    def parse_new_format_marker(
        self, lines: list[str], start_index: int
    ) -> tuple[Node | None, int]:
        """
        新記法 # キーワード # 形式のマーカーを解析

        Args:
            lines: All lines in the document
            start_index: Index of the marker line

        Returns:
            tuple: (parsed_node, next_index)
        """
        self.logger.debug(f"Parsing new format marker at line {start_index + 1}")
        if start_index >= len(lines):
            return None, start_index

        opening_line = lines[start_index].strip()
        self.logger.debug(f"Opening line: {opening_line}")

        # 新記法のマーカーパース
        parse_result = self.keyword_parser.marker_parser.parse_new_marker_format(
            opening_line
        )
        if parse_result is None:
            return None, start_index

        keywords, attributes, parse_errors = parse_result

        if parse_errors:
            self.logger.error(f"Parse errors in new format keywords: {parse_errors}")
            return error_node("; ".join(parse_errors), start_index + 1), start_index + 1

        # インライン内容を抽出
        inline_content = self.keyword_parser.marker_parser.extract_inline_content(
            opening_line
        )

        if inline_content:
            # インライン記法: # キーワード # 内容
            self.logger.debug(f"Processing inline content: {inline_content}")
            if len(keywords) == 1:
                node = self.keyword_parser.create_single_block(
                    keywords[0], inline_content, attributes
                )
            else:
                node = self.keyword_parser.create_compound_block(
                    keywords, inline_content, attributes
                )
            return node, start_index + 1
        else:
            # ブロック記法: # キーワード # \n 内容 \n ##
            return self._parse_new_format_block(
                lines, start_index, keywords, attributes
            )

    def _parse_new_format_block(
        self,
        lines: list[str],
        start_index: int,
        keywords: list[str],
        attributes: dict[str, Any],
    ) -> tuple[Node | None, int]:
        """
        新記法のブロック形式を解析

        Args:
            lines: All lines in the document
            start_index: Index of the opening marker
            keywords: Parsed keywords
            attributes: Parsed attributes

        Returns:
            tuple: (parsed_node, next_index)
        """
        self.logger.debug(f"Parsing new format block at line {start_index + 1}")

        # ブロック終了マーカーを探す
        end_index = None
        for i in range(start_index + 1, len(lines)):
            line = lines[i].strip()
            if self.keyword_parser.marker_parser.is_block_end_marker(line):
                end_index = i
                break

        if end_index is None:
            self.logger.error(f"Block end marker not found for line {start_index + 1}")
            return (
                error_node(
                    "ブロックの終了マーカー ## が見つかりません", start_index + 1
                ),
                start_index + 1,
            )

        # コンテンツを抽出
        content_lines = lines[start_index + 1 : end_index]
        content = "\n".join(content_lines).strip()
        self.logger.debug(f"Block content: {len(content)} characters")

        # 特殊キーワードの処理
        if "目次" in keywords:
            self.logger.info("Found TOC marker in new format")
            return toc_marker(), end_index + 1

        # ブロックノードを作成
        if len(keywords) == 1:
            self.logger.debug(f"Creating single block with keyword: {keywords[0]}")
            node = self.keyword_parser.create_single_block(
                keywords[0], content, attributes
            )
        else:
            self.logger.debug(f"Creating compound block with keywords: {keywords}")
            node = self.keyword_parser.create_compound_block(
                keywords, content, attributes
            )

        # 見出しIDの追加
        if any(keyword.startswith("見出し") for keyword in keywords):
            self.heading_counter += 1
            if hasattr(node, "add_attribute"):
                node.add_attribute("id", f"heading-{self.heading_counter}")
            self.logger.debug(f"Added heading ID: heading-{self.heading_counter}")

        self.logger.debug(
            f"New format block parsed successfully, next index: {end_index + 1}"
        )
        return node, end_index + 1

    def parse_block_marker(
        self, lines: list[str], start_index: int
    ) -> tuple[Node | None, int]:
        """
        Parse a block marker starting from the given index (new format only)

        Args:
            lines: All lines in the document
            start_index: Index of the opening marker

        Returns:
            tuple: (parsed_node, next_index)
        """
        # 新記法専用パーサーに委譲
        return self.parse_new_format_marker(lines, start_index)

    def _is_simple_image_marker(self, line: str) -> bool:
        """
        Check if a line is a simple image marker (# 画像 # filename.ext)
        """
        line = line.strip()

        # 新記法での画像マーカーチェック
        parse_result = self.keyword_parser.marker_parser.parse_new_marker_format(line)
        if parse_result is None:
            return False

        keywords, _, _ = parse_result

        # 画像キーワードが含まれているかチェック
        if "画像" not in keywords:
            return False

        # インライン内容があるかチェック（ファイル名）
        inline_content = self.keyword_parser.marker_parser.extract_inline_content(line)
        if not inline_content:
            return False

        # 画像拡張子チェック
        image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]
        return any(inline_content.lower().endswith(ext) for ext in image_extensions)

    def parse_paragraph(
        self, lines: list[str], start_index: int
    ) -> tuple[Node | None, int]:
        """
        Parse a paragraph starting from the given index

        Args:
            lines: All lines in the document
            start_index: Index where paragraph starts

        Returns:
            tuple: (paragraph_node, next_index)
        """
        self.logger.debug(f"Parsing paragraph at line {start_index + 1}")
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

            # Stop at block markers (new format)
            if self.is_block_marker_line(line):
                break

            paragraph_lines.append(line)
            current_index += 1

        if not paragraph_lines:
            return None, start_index

        # Join lines with space
        content = " ".join(paragraph_lines)
        self.logger.debug(
            f"Paragraph parsed: {len(content)} characters, {len(paragraph_lines)} lines"
        )

        return paragraph(content), current_index

    def is_block_marker_line(self, line: str) -> bool:
        """Check if a line is a block marker (new format only)"""
        line = line.strip()

        # 新記法チェック: # キーワード # または ##
        return self.keyword_parser.marker_parser.is_new_marker_format(
            line
        ) or self.keyword_parser.marker_parser.is_block_end_marker(line)

    def is_opening_marker(self, line: str) -> bool:
        """Check if a line is an opening block marker (new format only)"""
        line = line.strip()
        # 新記法: # キーワード # 形式（インライン・ブロック両対応）
        return self.keyword_parser.marker_parser.is_new_marker_format(line)

    def is_closing_marker(self, line: str) -> bool:
        """Check if a line is a closing block marker (new format only)"""
        return self.keyword_parser.marker_parser.is_block_end_marker(line)

    def skip_empty_lines(self, lines: list[str], start_index: int) -> int:
        """Skip empty lines and return the next non-empty line index"""
        index = start_index
        while index < len(lines) and not lines[index].strip():
            index += 1
        return index

    def find_next_significant_line(
        self, lines: list[str], start_index: int
    ) -> int | None:
        """Find the next line that contains significant content"""
        for i in range(start_index, len(lines)):
            line = lines[i].strip()
            if line and not self._is_comment_line(line):
                return i
        return None

    def _is_comment_line(self, line: str) -> bool:
        """Check if a line is a comment (starts with #)"""
        return line.strip().startswith("#")
