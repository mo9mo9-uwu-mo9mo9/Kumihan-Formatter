"""Refactored text parser for Kumihan-Formatter

This is the new, modular parser implementation that replaces the monolithic
parser.py file. Each parsing responsibility is now handled by specialized modules.
"""

from .core.ast_nodes import Node
from .core.block_parser import BlockParser
from .core.keyword_parser import KeywordParser
from .core.list_parser import ListParser
from .core.utilities.logger import get_logger


class Parser:
    """
    Kumihan記法のメインパーサー（各特化パーサーを統括）

    設計ドキュメント:
    - 記法仕様: /SPEC.md
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - KeywordParser: キーワード解析を委譲
    - ListParser: リスト解析を委譲（KeywordParser使用）
    - BlockParser: ブロック解析を委譲（KeywordParser使用）
    - Node: 生成するASTノード

    責務:
    - テキスト全体の解析フロー制御
    - 行タイプ判定と適切なパーサーへの委譲
    - AST構造の構築統括
    """

    def __init__(self, config=None) -> None:  # type: ignore
        """Initialize parser with fixed markers"""
        # 簡素化: configは無視して固定マーカーのみ使用
        self.config = None
        self.lines = []  # type: ignore
        self.current = 0
        self.errors = []  # type: ignore
        self.logger = get_logger(__name__)

        # Initialize specialized parsers
        self.keyword_parser = KeywordParser()
        self.list_parser = ListParser(self.keyword_parser)
        self.block_parser = BlockParser(self.keyword_parser)

        self.logger.debug("Parser initialized with specialized parsers")

    def parse(self, text: str) -> list[Node]:
        """
        Parse text into AST nodes

        Args:
            text: Input text to parse

        Returns:
            list[Node]: Parsed AST nodes
        """
        self.lines = text.split("\n")
        self.current = 0
        self.errors = []
        nodes = []

        self.logger.info(f"Starting parse of {len(self.lines)} lines")
        self.logger.debug(f"Input text length: {len(text)} characters")

        while self.current < len(self.lines):
            node = self._parse_line()

            if node:
                nodes.append(node)
                self.logger.debug(
                    f"Parsed node type: {node.type} at line {self.current}"
                )

        self.logger.info(
            f"Parse complete: {len(nodes)} nodes created, {len(self.errors)} errors"
        )
        return nodes

    def _parse_line(self) -> Node | None:
        """Parse a single line or block starting from current position"""
        if self.current >= len(self.lines):
            return None

        # Skip empty lines
        self.current = self.block_parser.skip_empty_lines(self.lines, self.current)

        if self.current >= len(self.lines):
            return None

        line = self.lines[self.current].strip()
        self.logger.debug(
            f"Processing line {self.current}: {line[:50]}..."
            if len(line) > 50
            else f"Processing line {self.current}: {line}"
        )

        # Parse block markers first (to handle new notation #keyword#)
        if self.block_parser.is_opening_marker(line):
            self.logger.debug(f"Found block marker at line {self.current}")
            node, next_index = self.block_parser.parse_block_marker(
                self.lines, self.current
            )
            self.current = next_index
            return node

        # Skip comment lines (lines starting with # but not new notation)
        # This check is now after block marker check to avoid conflict
        if line.startswith("#") and not self.block_parser.is_opening_marker(line):
            self.current += 1
            return None

        # Parse lists
        list_type = self.list_parser.is_list_line(line)
        if list_type:
            self.logger.debug(f"Found {list_type} list at line {self.current}")
            if list_type == "ul":
                node, next_index = self.list_parser.parse_unordered_list(
                    self.lines, self.current
                )
            else:  # 'ol'
                node, next_index = self.list_parser.parse_ordered_list(
                    self.lines, self.current
                )

            self.current = next_index
            return node

        # Parse paragraph
        node, next_index = self.block_parser.parse_paragraph(self.lines, self.current)
        self.current = next_index
        return node

    def get_errors(self) -> list[str]:
        """Get parsing errors"""
        return self.errors

    def add_error(self, error: str) -> None:
        """Add a parsing error"""
        self.errors.append(error)
        self.logger.warning(f"Parse error: {error}")

    def get_statistics(self) -> dict:  # type: ignore
        """Get parsing statistics"""
        return {
            "total_lines": len(self.lines),
            "errors_count": len(self.errors),
            "heading_count": self.block_parser.heading_counter,
        }


def parse(text: str, config=None) -> list[Node]:  # type: ignore
    """
    Main parsing function (compatibility with existing API)

    Args:
        text: Input text to parse
        config: Optional configuration

    Returns:
        list[Node]: Parsed AST nodes
    """
    parser = Parser(config)
    return parser.parse(text)
