"""Block notation handling for Kumihan parser - Issue #813 refactoring

This module contains block notation parsing logic extracted from the
monolithic parser.py. Handles block markers, paragraphs, and optimized
block processing.
"""

from typing import Any, Optional

from .core.ast_nodes import Node
from .core.utilities.logger import get_logger


class BlockHandler:
    """
    ブロック記法処理の特化ハンドラー

    担当範囲：
    - ブロックマーカー高速処理
    - パラグラフ処理
    - フォールバック処理
    - 最適化された行解析
    """

    def __init__(self, parser_instance: Any) -> None:
        """
        Args:
            parser_instance: メインParserインスタンス（依存注入）
        """
        self.parser = parser_instance
        self.logger = get_logger(__name__)

    def parse_block_marker_fast(self, lines: list[str], current: int) -> tuple[Optional[Node], int]:
        """高速ブロックマーカー解析"""
        node, next_index = self.parser.block_parser.parse_block_marker(lines, current)
        return node, next_index

    def parse_paragraph_fast(self, lines: list[str], current: int) -> tuple[Optional[Node], int]:
        """高速パラグラフ解析"""
        node, next_index = self.parser.block_parser.parse_paragraph(lines, current)
        return node, next_index

    def parse_line_fallback(self, lines: list[str], current: int) -> tuple[Optional[Node], int]:
        """フォールバック処理（従来ロジック）"""
        if current >= len(lines):
            return None, current + 1

        line = lines[current].strip()

        if self.parser.block_parser.is_opening_marker(line):
            node, next_index = self.parser.block_parser.parse_block_marker(lines, current)
            return node, next_index

        return None, current + 1

    def parse_line_optimized(
        self,
        line_types: dict[int, str],
        pattern_cache: dict[str, Any],
        line_type_cache: dict[str, Any],
        current: int,
    ) -> Optional[Node]:
        """
        Issue #757対応: 最適化されたライン解析

        事前解析結果を活用した高速ライン処理
        """
        if current >= len(self.parser.lines):
            return None

        line_type = line_types.get(current, "unknown")

        # タイプ別高速処理
        if line_type == "empty":
            self.parser.current += 1
            return None
        elif line_type == "block_marker":
            return self._parse_block_marker_fast_internal()
        elif line_type == "comment":
            self.parser.current += 1
            return None
        elif line_type == "paragraph":
            return self._parse_paragraph_fast_internal()
        else:
            # フォールバック
            return self._parse_line_fallback_internal()

    def _parse_block_marker_fast_internal(self) -> Optional[Node]:
        """内部用高速ブロックマーカー解析"""
        node, next_index = self.parser.block_parser.parse_block_marker(
            self.parser.lines, self.parser.current
        )
        self.parser.current = next_index
        return node  # type: ignore[no-any-return]

    def _parse_paragraph_fast_internal(self) -> Optional[Node]:
        """内部用高速パラグラフ解析"""
        node, next_index = self.parser.block_parser.parse_paragraph(
            self.parser.lines, self.parser.current
        )
        self.parser.current = next_index
        return node  # type: ignore[no-any-return]

    def _parse_line_fallback_internal(self) -> Optional[Node]:
        """内部用フォールバック処理"""
        line = self.parser.lines[self.parser.current].strip()

        if self.parser.block_parser.is_opening_marker(line):
            node, next_index = self.parser.block_parser.parse_block_marker(
                self.parser.lines, self.parser.current
            )
            self.parser.current = next_index
            return node  # type: ignore[no-any-return]

        self.parser.current += 1
        return None

    def analyze_line_types_batch(self, lines: list[str]) -> dict[int, str]:
        """
        Issue #757対応: 一括行タイプ解析（O(n)処理）

        全行のタイプを事前に解析することで、後続処理を高速化
        """
        line_types = {}

        for i, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                line_types[i] = "empty"
            elif self.parser.block_parser.is_opening_marker(stripped):
                line_types[i] = "block_marker"
            elif stripped.startswith("#") and not self.parser.block_parser.is_opening_marker(
                stripped
            ):
                line_types[i] = "comment"
            elif self.parser.list_parser.is_list_line(stripped):
                line_types[i] = "list"
            else:
                line_types[i] = "paragraph"

        return line_types
