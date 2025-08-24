"""Content Parser - 統合コンテンツ解析エンジン（メインクラス）

責任分離による構造:
- このファイル: メインクラス・パブリックインターフェース・プロトコル準拠
- content_handlers.py: 処理・分析ロジック
- content_utils.py: ユーティリティ関数群
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from ...core.parsing.base.parser_protocols import (
        ParseResult,
        ParseContext,
        BaseParserProtocol,
    )
else:
    try:
        from ...core.parsing.base.parser_protocols import (
            ParseResult,
            ParseContext,
            BaseParserProtocol,
        )
    except ImportError:
        BaseParserProtocol = object

from ...core.utilities.logger import get_logger
from .content_handlers import ContentHandler, ContentAnalyzer
from .content_utils import (
    setup_content_patterns,
    setup_content_classifiers,
    setup_structure_analyzers,
    extract_footnotes_from_text,
    parse_footnotes,
    extract_inline_content,
    is_new_marker_format,
    is_block_end_marker,
    normalize_marker_syntax,
)


class UnifiedContentParser(BaseParserProtocol):
    """統合コンテンツ解析エンジン - BaseParserProtocol実装

    責任範囲:
    - プロトコル準拠インターフェース実装
    - コンテンツ解析の統合管理
    - 外部依存関係の管理

    分離された処理:
    - 詳細な分析処理: ContentHandler, ContentAnalyzer
    - ユーティリティ関数: content_utils モジュール
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

        # コア解析エンジンの初期化
        try:
            from ...core.parsing.get_global_coordinator import get_global_coordinator

            self.core_parser = get_global_coordinator()
        except ImportError:
            self.core_parser = None

        # 責任分離されたハンドラの初期化
        self.content_handler = ContentHandler()
        self.content_analyzer = ContentAnalyzer()

        # 設定の初期化（ユーティリティ関数を使用）
        self.content_patterns = setup_content_patterns()
        self.content_classifiers = setup_content_classifiers()
        self.structure_analyzers = setup_structure_analyzers()

    # === BaseParserProtocol実装 ===

    def parse(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> "ParseResult":
        """統一コンテンツ解析 - BaseParserProtocol準拠"""
        from ...core.parsing.base.parser_protocols import ParseResult

        try:
            self.logger.debug("統合コンテンツ解析開始")

            # コンテンツの前処理
            normalized_content = normalize_marker_syntax(content)

            # コア解析の実行
            if self.core_parser:
                core_result = self.core_parser.parse_content(normalized_content)
                nodes = core_result.get("nodes", [])
            else:
                # フォールバック処理
                nodes = self._fallback_parse(normalized_content)

            # 詳細解析の実行（ハンドラに委譲）
            classification = self.content_handler.classify_content(normalized_content)
            structure_analysis = self.content_handler.analyze_content_structure(
                normalized_content
            )
            entity_analysis = self.content_handler.analyze_entities(
                normalized_content, self.content_patterns
            )
            semantic_analysis = self.content_handler.analyze_semantic_structure(
                normalized_content, self.content_patterns
            )

            # ParseResult作成
            return ParseResult(
                success=True,
                nodes=nodes,
                errors=[],
                warnings=[],
                metadata={
                    "parser_type": "UnifiedContentParser",
                    "content_classification": classification,
                    "structure_analysis": structure_analysis,
                    "entity_analysis": entity_analysis,
                    "semantic_analysis": semantic_analysis,
                    "processing_time": 0.0,
                },
            )

        except Exception as e:
            self.logger.error(f"統合コンテンツ解析エラー: {e}")
            return self._create_error_parse_result(str(e), content)

    def validate(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """コンテンツバリデーション - BaseParserProtocol準拠"""
        errors = []

        try:
            # 基本的な構造検証（ハンドラに委譲）
            structure_errors = self.content_handler.validate_content_structure(content)
            errors.extend(structure_errors)

        except Exception as e:
            self.logger.error(f"バリデーション処理エラー: {e}")
            errors.append(f"バリデーション処理中にエラーが発生しました: {e}")

        return errors

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得 - BaseParserProtocol準拠"""
        return {
            "name": "UnifiedContentParser",
            "version": "3.0.0",
            "description": "統合コンテンツ解析エンジン",
            "supported_formats": [
                "kumihan",
                "markdown",
                "plain_text",
                "mixed_content",
                "footnotes",
                "semantic_markup",
            ],
            "capabilities": [
                "content_classification",
                "structure_analysis",
                "entity_extraction",
                "semantic_analysis",
                "footnote_processing",
                "inline_content_processing",
            ],
            "architecture": "responsibility_separated",
            "components": ["ContentHandler", "ContentAnalyzer", "content_utils"],
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応確認 - BaseParserProtocol準拠"""
        supported = ["kumihan", "markdown", "text", "mixed", "footnote", "semantic"]
        return any(fmt in format_hint.lower() for fmt in supported)

    # === プライベートメソッド（処理詳細） ===

    def _fallback_parse(self, content: str) -> List[Any]:
        """フォールバック解析処理"""
        try:
            from ...core.ast_nodes.node import Node

            # 簡単なテキストノード作成
            return [Node("text", content=content)]
        except ImportError:
            # 最終フォールバック
            return [{"type": "text", "content": content}]

    def _create_error_parse_result(
        self, error_msg: str, original_content: str
    ) -> "ParseResult":
        """エラー時のParseResult作成"""
        from ...core.parsing.base.parser_protocols import ParseResult

        return ParseResult(
            success=False,
            nodes=[],
            errors=[error_msg],
            warnings=[],
            metadata={
                "parser_type": "UnifiedContentParser",
                "original_content_length": len(original_content),
                "error_occurred": True,
            },
        )

    # === 公開メソッド（専用機能） ===

    def parse_mixed_content(self, content: str) -> Dict[str, Any]:
        """混合コンテンツ解析（分析器に委譲）"""
        return self.content_analyzer.parse_mixed_content(content)

    def extract_text_summary(self, parse_result: "ParseResult") -> Dict[str, Any]:
        """テキストサマリー抽出（分析器に委譲）"""
        return self.content_analyzer.extract_text_summary(parse_result)

    def suggest_improvements(self, parse_result: "ParseResult") -> List[str]:
        """改善提案生成（分析器に委譲）"""
        return self.content_analyzer.suggest_improvements(parse_result)

    def get_content_statistics(self, content: str) -> Dict[str, Any]:
        """コンテンツ統計取得（分析器に委譲）"""
        return self.content_analyzer.get_content_statistics(content)

    def extract_footnotes_from_text(
        self, content: str
    ) -> tuple[str, List[Dict[str, str]]]:
        """脚注抽出（ユーティリティ関数に委譲）"""
        return extract_footnotes_from_text(content)

    def parse_footnotes(self, footnotes_data: List[Dict[str, str]]) -> Dict[str, str]:
        """脚注解析（ユーティリティ関数に委譲）"""
        return parse_footnotes(footnotes_data)

    def extract_inline_content(self, content: str) -> List[Dict[str, Any]]:
        """インラインコンテンツ抽出（ユーティリティ関数に委譲）"""
        return extract_inline_content(content)

    def is_new_marker_format(self, line: str) -> bool:
        """新マーカーフォーマット判定（ユーティリティ関数に委譲）"""
        return is_new_marker_format(line)

    def is_block_end_marker(self, line: str) -> bool:
        """ブロック終了マーカー判定（ユーティリティ関数に委譲）"""
        return is_block_end_marker(line)

    def normalize_marker_syntax(self, content: str) -> str:
        """マーカー構文正規化（ユーティリティ関数に委譲）"""
        return normalize_marker_syntax(content)


# 後方互換性のためのエイリアス
ContentParser = UnifiedContentParser
