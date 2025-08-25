"""Unified Block Parser - Main class implementation

このモジュールはブロックパーサーのメインクラスとプロトコル実装を提供します。
責任分離により、処理ロジックとユーティリティは別モジュールに分離されています。
"""

import warnings
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from ...core.ast_nodes.node import Node
from ...core.ast_nodes import create_node
from ...core.parsing.base.parser_protocols import (
    KeywordParserProtocol,
    ParseContext,
    ParseResult,
    create_parse_result,
)
from ...core.utilities.logger import get_logger

from .handlers import BlockHandler
from .utils import (
    BlockPatterns,
    find_next_block_end,
    has_matching_closing_marker,
    is_block_marker_format,
    is_new_format_marker,
    preprocess_lines,
    validate_block_structure,
)

if TYPE_CHECKING:
    from ..keyword.keyword_parser import KeywordParser


class UnifiedBlockParser:
    """統合ブロックパーサー - Issue #1173対応 責任分離最適化版

    メインクラス・プロトコル実装・公開API（150-200行目標）

    機能:
    - ブロック解析のコア実装
    - プロトコル準拠
    - 公開API提供
    - エラー・警告管理
    """

    def __init__(self, keyword_parser: Optional[Any] = None) -> None:
        self.logger = get_logger(__name__)

        # キーワードパーサー設定
        from .utils import get_keyword_parser

        self.keyword_parser = keyword_parser or get_keyword_parser()

        # ハンドラー・プロセッサー初期化
        from .handlers import BlockProcessingEngine

        self.processing_engine = BlockProcessingEngine()

        # 基本設定
        self.heading_counter = 0
        self.parser_ref = None

    def parse(
        self,
        content: Union[str, List[str]],
        context: Optional["ParseContext"] = None,
        **kwargs: Any,
    ) -> "ParseResult":
        """統一パースメソッド - プロトコル準拠"""
        try:
            # キャッシュ確認
            from .utils import create_cache_key

            cache_key = create_cache_key(content, context)

            cached_result = self.processing_engine.get_cached_result(cache_key)
            if cached_result:
                return cached_result

            # エラー・警告クリア
            self.processing_engine.clear_errors_warnings()

            # コンテンツ正規化・解析
            if isinstance(content, list):
                nodes = self.processing_engine.parse_content_lines(content)
            else:
                nodes = [self.processing_engine.parse_implementation(content)]

            # ParseResult作成
            result = create_parse_result(
                nodes=[n for n in nodes if n is not None],
                success=True,
                errors=self.processing_engine.get_errors(),
                warnings=self.processing_engine.get_warnings(),
                metadata={
                    "parser_type": "block",
                    "block_count": len(nodes) if nodes else 0,
                },
            )

            # キャッシュ保存
            self.processing_engine.set_cached_result(cache_key, result)
            return result

        except Exception as e:
            self.logger.error(f"Block parsing error: {e}")
            return create_parse_result(
                nodes=[],
                success=False,
                errors=[f"Block parsing failed: {e}"],
                warnings=[],
                metadata={"parser_type": "block"},
            )

    def get_errors(self) -> List[str]:
        """エラー一覧取得"""
        return self.processing_engine.get_errors()

    def get_warnings(self) -> List[str]:
        """警告一覧取得"""
        return self.processing_engine.get_warnings()

    def set_parser_reference(self, parser: Any) -> None:
        """パーサー参照設定"""
        self.parser_ref = parser
        self.processing_engine.set_parser_reference(parser)

    # === BlockParserProtocol実装 ===

    def parse_block(
        self, block: str, context: Optional["ParseContext"] = None
    ) -> "Node":
        """単一ブロックをパース（プロトコル準拠）"""
        try:
            return self.processing_engine.parse_single_block(block) or create_node(
                "empty", content=""
            )
        except Exception as e:
            self.logger.error(f"Single block parsing error: {e}")
            return create_node("error", content=f"Block parsing failed: {e}")

    def extract_blocks(
        self, text: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """テキストからブロックを抽出（プロトコル準拠）"""
        return self.processing_engine.extract_blocks(text, context)

    def detect_block_type(self, block: str) -> Optional[str]:
        """ブロックタイプを検出（プロトコル準拠）"""
        return self.processing_engine.detect_block_type(block)

    # === レガシー互換性ヘルパー ===

    def is_block_marker_line(self, line: str) -> bool:
        """ブロックマーカー行判定"""
        from .utils import is_block_marker_line

        return is_block_marker_line(line)

    def is_opening_marker(self, line: str) -> bool:
        """開始マーカー判定"""
        from .utils import is_opening_marker

        return is_opening_marker(line)

    def is_closing_marker(self, line: str) -> bool:
        """終了マーカー判定"""
        from .utils import is_closing_marker

        return is_closing_marker(line)

    def skip_empty_lines(self, lines: List[str], start_index: int) -> int:
        """空行をスキップ"""
        from .utils import skip_empty_lines

        return skip_empty_lines(lines, start_index)

    def find_next_significant_line(self, lines: List[str], start_index: int) -> int:
        """次の意味のある行を検索"""
        from .utils import find_next_significant_line

        return find_next_significant_line(lines, start_index)

    def validate(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """ブロック構文チェック"""
        return self.processing_engine.validate(content, context)

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報（プロトコル準拠）"""
        return self.processing_engine.get_parser_info()

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        return self.processing_engine.supports_format(format_hint)


# Legacy alias for backward compatibility
BlockParser = UnifiedBlockParser
