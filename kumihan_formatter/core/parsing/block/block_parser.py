"""Block parsing utilities for Kumihan-Formatter

This module handles the parsing of basic block-level elements.
新記法 #キーワード# 対応 - Issue #665

⚠️  DEPRECATION NOTICE - Issue #880 Phase 2C:
このBlockParserは非推奨です。新しい統一パーサーシステムをご利用ください:
from kumihan_formatter.core.parsing import (
    get_global_coordinator,
    register_default_parsers,
)
"""

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from ...ast_nodes import Node

# 統一プロトコルインポート
from ..base.parser_protocols import (
    BaseParserProtocol,
    BlockParserProtocol,
    ParseContext,
    ParseError,
    ParseResult,
)

if TYPE_CHECKING:
    from ..base.parser_protocols import KeywordParserProtocol
    from ..keyword.keyword_parser import KeywordParser
else:
    try:
        from ..base.parser_protocols import KeywordParserProtocol
    except ImportError:
        from typing import Protocol

        KeywordParserProtocol = Protocol


class BlockParser:
    """Main block parser that integrates specialized parsers.

    This class maintains API compatibility while delegating functionality
    to specialized parser components for better maintainability.

    Refactored: 2025-08-10 (Error問題修正 - 711行から軽量化)
    Issue #914 Phase 2: 循環参照解消 - KeywordParser直接依存を削除
    """

    def __init__(
        self, keyword_parser: Optional["KeywordParserProtocol"] = None
    ) -> None:
        """Initialize block parser with specialized components.

        Args:
            keyword_parser: Optional keyword parser instance (protocol-based)

        ⚠️  DEPRECATION WARNING:
        BlockParser is deprecated. Use kumihan_formatter.core.parsing instead.
        """
        # 非推奨警告
        import warnings

        warnings.warn(
            "BlockParser is deprecated and will be removed in v3.0. "
            "Use kumihan_formatter.core.parsing.get_global_coordinator() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        from kumihan_formatter.core.utilities.logger import get_logger

        from .base_parser import BaseBlockParser
        from .content_parser import ContentParser
        from .marker_parser import MarkerBlockParser
        from .text_parser import TextBlockParser

        self.logger = get_logger(__name__)

        # 依存関係注入: KeywordParserをDIコンテナから取得
        if keyword_parser is None:
            self.keyword_parser = self._get_keyword_parser()
        else:
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

        # Issue #914: 統一プロトコル対応用キャッシュ
        self._processed_content_cache: Dict[str, ParseResult] = {}

    def _get_keyword_parser(self) -> Optional["KeywordParserProtocol"]:
        """DIコンテナからKeywordParserを取得

        Issue #914 Phase 2: 依存関係注入パターン

        Returns:
            KeywordParserProtocol instance or None
        """
        try:
            from ...patterns.dependency_injection import get_container

            container = get_container()
            return container.resolve(KeywordParserProtocol)
        except Exception as e:
            self.logger.warning(f"KeywordParser取得失敗、フォールバック使用: {e}")
            # フォールバック: specialized/keyword_parser.pyから直接インポート
            try:
                from ..specialized.keyword_parser import UnifiedKeywordParser

                return UnifiedKeywordParser()
            except Exception as fallback_error:
                self.logger.error(f"フォールバックも失敗: {fallback_error}")
                return None

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

    # === 統一プロトコル実装: BaseParserProtocol ===

    def parse(
        self, content: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """統一パースインターフェース

        Args:
            content: パース対象のコンテンツ
            context: パースコンテキスト（オプション）

        Returns:
            ParseResult: 統一パース結果
        """
        try:
            # キャッシュ確認
            cache_key = f"{hash(content)}_{id(context) if context else 0}"
            if cache_key in self._processed_content_cache:
                return self._processed_content_cache[cache_key]

            # ブロック抽出・パース
            blocks = self.extract_blocks(content, context)
            nodes = []

            for block in blocks:
                try:
                    node = self.parse_block(block, context)
                    if node:
                        nodes.append(node)
                except Exception as e:
                    self.logger.warning(f"ブロックパース失敗: {e}")
                    # エラーノードを作成
                    error_node = Node(
                        type="error_block", content=block, attributes={"error": str(e)}
                    )
                    nodes.append(error_node)

            # ParseResult作成
            result = ParseResult(
                success=len(nodes) > 0,
                nodes=nodes,
                errors=[],
                warnings=[],
                metadata={
                    "parser": "BlockParser",
                    "block_count": len(blocks),
                    "node_count": len(nodes),
                },
            )

            # キャッシュ保存
            self._processed_content_cache[cache_key] = result
            return result

        except Exception as e:
            return ParseResult(
                success=False,
                nodes=[],
                errors=[f"Block parsing failed: {str(e)}"],
                warnings=[],
                metadata={"parser": "BlockParser"},
            )

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """バリデーション - ブロック構文チェック

        Args:
            content: 検証対象のコンテンツ
            context: 検証コンテキスト（オプション）

        Returns:
            List[str]: エラーメッセージリスト（空リストは成功）
        """
        errors = []

        if not isinstance(content, str):
            errors.append("Content must be a string")
            return errors

        if not content.strip():
            errors.append("Empty content provided")
            return errors

        try:
            # ブロック抽出試行
            blocks = self.extract_blocks(content, context)

            # 各ブロックの妥当性検証
            for i, block in enumerate(blocks):
                block_type = self.detect_block_type(block)
                if block_type is None:
                    errors.append(f"Block {i+1}: Unknown block type")

                # マーカー整合性チェック
                if self.is_opening_marker(
                    block
                ) and not self._has_matching_closing_marker(block):
                    errors.append(f"Block {i+1}: Missing closing marker")

        except Exception as e:
            errors.append(f"Block validation failed: {str(e)}")

        return errors

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得

        Returns:
            Dict[str, Any]: パーサーメタデータ
        """
        return {
            "name": "BlockParser",
            "version": "2.0",
            "supported_formats": ["kumihan_block", "marker_block", "text_block"],
            "capabilities": [
                "block_parsing",
                "marker_detection",
                "text_processing",
                "nested_blocks",
                "validation",
            ],
            "description": "Block-level element parser for Kumihan-Formatter",
            "author": "Kumihan-Formatter Project",
            "deprecation_notice": (
                "This parser is deprecated. Use kumihan_formatter.core.parsing instead."
            ),
        }

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定

        Args:
            format_hint: フォーマットヒント文字列

        Returns:
            bool: 対応可能かどうか
        """
        supported = {"kumihan_block", "marker_block", "text_block", "block"}
        return format_hint.lower() in supported

    # === 統一プロトコル実装: BlockParserProtocol ===

    def parse_block(self, block: str, context: Optional[ParseContext] = None) -> Node:
        """単一ブロックをパース

        Args:
            block: パース対象のブロック
            context: パースコンテキスト（オプション）

        Returns:
            Node: パース結果のノード

        Raises:
            ParseError: ブロックパース中のエラー
        """
        try:
            lines = block.split("\n")

            # ブロックタイプ検出
            block_type = self.detect_block_type(block)

            if block_type == "marker_block":
                # マーカーブロック処理
                node, _ = self.parse_block_marker(lines, 0)
                return node
            elif block_type == "text_block":
                # テキストブロック処理
                node, _ = self.parse_paragraph(lines, 0)
                return node
            else:
                # 汎用ブロック処理
                return Node(
                    type="generic_block",
                    content=block.strip(),
                    attributes={"block_type": block_type or "unknown"},
                )

        except Exception as e:
            raise ParseError(f"Failed to parse block: {str(e)}")

    def extract_blocks(
        self, text: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """テキストからブロックを抽出

        Args:
            text: 抽出対象のテキスト
            context: 抽出コンテキスト（オプション）

        Returns:
            List[str]: 抽出されたブロックのリスト
        """
        blocks = []
        lines = text.split("\n")
        current_block: List[str] = []
        in_block = False

        for line in lines:
            if self.is_opening_marker(line):
                # 新しいブロック開始
                if current_block:
                    blocks.append("\n".join(current_block))
                current_block = [line]
                in_block = True
            elif self.is_closing_marker(line):
                # ブロック終了
                current_block.append(line)
                blocks.append("\n".join(current_block))
                current_block = []
                in_block = False
            elif in_block:
                # ブロック内容
                current_block.append(line)
            else:
                # 通常テキスト
                if line.strip():  # 空行でない場合
                    if current_block:
                        current_block.append(line)
                    else:
                        current_block = [line]
                else:
                    # 空行でブロック区切り
                    if current_block:
                        blocks.append("\n".join(current_block))
                        current_block = []

        # 最後のブロック処理
        if current_block:
            blocks.append("\n".join(current_block))

        return [block for block in blocks if block.strip()]

    def detect_block_type(self, block: str) -> Optional[str]:
        """ブロックタイプを検出

        Args:
            block: 検査対象のブロック

        Returns:
            Optional[str]: 検出されたブロックタイプ（None=未検出）
        """
        lines = block.split("\n")
        if not lines:
            return None

        first_line = lines[0].strip()

        # マーカーブロック判定
        if self.is_block_marker_line(first_line):
            return "marker_block"

        # 新形式マーカー判定
        if self._is_new_format_marker(first_line):
            return "new_format_marker"

        # リストブロック判定
        if self._is_list_internal(first_line):
            return "list_block"

        # テキストブロック（デフォルト）
        return "text_block"

    # === ヘルパーメソッド ===

    def _has_matching_closing_marker(self, block: str) -> bool:
        """対応する閉じマーカーがあるかチェック"""
        lines = block.split("\n")
        opening_count = sum(1 for line in lines if self.is_opening_marker(line))
        closing_count = sum(1 for line in lines if self.is_closing_marker(line))
        return opening_count == closing_count

    def _is_new_format_marker(self, line: str) -> bool:
        """新形式マーカー判定"""
        return line.startswith("#") and line.endswith("#") and len(line) > 2
