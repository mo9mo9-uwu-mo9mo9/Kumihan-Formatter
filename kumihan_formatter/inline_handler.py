"""Inline notation handling for Kumihan parser - Issue #813 refactoring

This module contains inline notation parsing logic extracted from the monolithic parser.py.
Handles list processing and other inline elements.
"""

from typing import Optional

from .core.ast_nodes import Node
from .core.utilities.logger import get_logger


class InlineHandler:
    """
    インライン記法処理の特化ハンドラー

    担当範囲：
    - リスト処理（順序付き・順序なし）
    - インライン要素処理
    - 高速リスト解析
    """

    def __init__(self, parser_instance):
        """
        Args:
            parser_instance: メインParserインスタンス（依存注入）
        """
        self.parser = parser_instance
        self.logger = get_logger(__name__)

    def parse_list_fast(
        self, lines: list[str], current: int
    ) -> tuple[Optional[Node], int]:
        """高速リスト解析"""
        if current >= len(lines):
            return None, current + 1

        line = lines[current].strip()
        list_type = self.parser.list_parser.is_list_line(line)

        if list_type == "ul":
            node, next_index = self.parser.list_parser.parse_unordered_list(
                lines, current
            )
        else:
            node, next_index = self.parser.list_parser.parse_ordered_list(
                lines, current
            )

        return node, next_index

    def parse_list_fast_internal(self) -> Optional[Node]:
        """内部用高速リスト解析（current位置を自動更新）"""
        line = self.parser.lines[self.parser.current].strip()
        list_type = self.parser.list_parser.is_list_line(line)

        if list_type == "ul":
            node, next_index = self.parser.list_parser.parse_unordered_list(
                self.parser.lines, self.parser.current
            )
        else:
            node, next_index = self.parser.list_parser.parse_ordered_list(
                self.parser.lines, self.parser.current
            )

        self.parser.current = next_index
        return node

    def is_list_line(self, line: str) -> str | None:
        """リスト行判定の委譲メソッド"""
        return self.parser.list_parser.is_list_line(line)

    def parse_unordered_list(
        self, lines: list[str], current: int
    ) -> tuple[Optional[Node], int]:
        """順序なしリスト解析の委譲メソッド"""
        return self.parser.list_parser.parse_unordered_list(lines, current)

    def parse_ordered_list(
        self, lines: list[str], current: int
    ) -> tuple[Optional[Node], int]:
        """順序付きリスト解析の委譲メソッド"""
        return self.parser.list_parser.parse_ordered_list(lines, current)

    def handle_list_with_graceful_errors(
        self, line: str, current: int
    ) -> tuple[Optional[Node], int]:
        """graceful error handling対応のリスト処理"""
        try:
            # Parse lists
            list_type = self.parser.list_parser.is_list_line(line)
            if list_type:
                self.logger.debug(f"Found {list_type} list at line {current}")
                if list_type == "ul":
                    node, next_index = self.parser.list_parser.parse_unordered_list(
                        self.parser.lines, current
                    )
                else:  # 'ol'
                    node, next_index = self.parser.list_parser.parse_ordered_list(
                        self.parser.lines, current
                    )

                return node, next_index

        except Exception as e:
            # リスト解析エラーを記録して継続
            self.parser._record_graceful_error(
                current + 1,
                1,
                "list_parse_error",
                "error",
                f"リスト解析エラー: {str(e)}",
                line,
                "リスト記法を確認してください",
            )
            return self.parser._create_error_node(line, str(e)), current + 1

        return None, current
