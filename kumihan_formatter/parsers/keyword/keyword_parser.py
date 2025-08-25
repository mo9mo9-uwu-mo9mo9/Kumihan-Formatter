"""Keyword Parser - 統合キーワード解析エンジン（分割最適化版）

責任分離による構造:
- このファイル: メインクラス・コア解析ロジック・プロトコル準拠
- keyword_handlers.py: 各種キーワードハンドラー・処理ロジック
- keyword_utils.py: ユーティリティ・パターンマッチング・キャッシュ

統合機能:
- 全Kumihanキーワード解析（基本・高度・カスタム）
- プロトコル準拠 (KeywordParserProtocol)
- 後方互換性維持
"""

from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.parsing.base.parser_protocols import (
        ParseResult,
        ParseContext,
        KeywordParserProtocol,
    )
    from ...core.ast_nodes import Node
else:
    try:
        from ...core.parsing.base.parser_protocols import (
            ParseResult,
            ParseContext,
            KeywordParserProtocol,
        )
        from ...core.ast_nodes import Node, create_node
    except ImportError:
        KeywordParserProtocol = object
        Node = None
        create_node = None

from ...core.parsing.base import UnifiedParserBase, CompositeMixin
from ...core.parsing.base.parser_protocols import create_parse_result
from ...core.parsing.protocols import ParserType
from ...core.utilities.logger import get_logger

from .keyword_config import KeywordParserConfig
from .keyword_validation import KeywordValidator


class UnifiedKeywordParser(UnifiedParserBase, CompositeMixin, KeywordParserProtocol):
    """統合キーワードパーサー - 分割最適化版

    分割されたコンポーネントを統合し、既存API完全互換性を維持:
    - BasicKeywordHandler: 基本キーワード（太字・イタリック・見出し・コード）
    - AdvancedKeywordHandler: 高度キーワード（リスト・表・引用・脚注）
    - CustomKeywordHandler: カスタム・ユーザー定義キーワード・拡張機能
    - AttributeProcessor: 属性解析・スタイル適用・CSSクラス処理
    - KeywordExtractor: キーワード抽出・解析ロジック
    - KeywordCache: パフォーマンス最適化キャッシュ

    機能:
    - Kumihanキーワード全種類（太字・イタリック・見出し・コード・リスト等）
    - カスタムキーワード定義・拡張
    - 属性・スタイル・CSSクラス適用
    - バリデーション・エラー回復・修正提案
    - プロトコル準拠・高性能キャッシュ
    """

    def __init__(self) -> None:
        super().__init__(parser_type=ParserType.KEYWORD)

        self.logger = get_logger(__name__)

        # 設定管理の委譲
        self.config = KeywordParserConfig()

        # 設定からの値取得
        self.keyword_definitions = self.config.keyword_definitions
        self.basic_keywords = self.config.get_basic_keywords()
        self.advanced_keywords = self.config.get_advanced_keywords()
        self.all_keywords = self.config.get_all_keywords()

        # ハンドラー群の取得
        self.keyword_handlers = self.config.get_handlers()

        # コンポーネントの取得
        self.basic_handler = self.config.basic_handler
        self.advanced_handler = self.config.advanced_handler
        self.custom_handler = self.config.custom_handler
        self.attribute_processor = self.config.attribute_processor
        self.keyword_extractor = self.config.keyword_extractor
        self.info_processor = self.config.info_processor
        self.validator_collection = self.config.validator_collection
        self.cache = self.config.cache

        # バリデーター初期化
        self.validator = KeywordValidator(self.config)

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> "Node":
        """基底クラス用の解析実装（UnifiedParserBase準拠）"""
        text = self.info_processor.normalize_content(content)

        try:
            # キーワード抽出・解析
            keyword_info = self.keyword_extractor.extract_keyword_info(text)
            if not keyword_info:
                return create_node("text", content=text)

            # キーワード処理
            return self._process_keyword(keyword_info)

        except Exception as e:
            self.logger.error(f"Keyword parsing failed: {e}")
            return create_node("error", content=f"Keyword parsing failed: {e}")

    def _process_keyword(self, keyword_info: Dict[str, Any]) -> "Node":
        """キーワード情報を処理してNodeを生成"""
        keywords = keyword_info["keywords"]
        content = keyword_info["content"]
        format_type = keyword_info["format"]

        # 最初のキーワードをメインキーワードとして処理
        if not keywords:
            return create_node("text", content=content)

        main_keyword = keywords[0]
        handler = self.keyword_handlers.get(
            main_keyword, self.custom_handler.handle_unknown_keyword
        )

        # ハンドラー実行
        node = handler(content, keywords, format_type)

        # 属性処理
        self.attribute_processor.apply_keyword_attributes(node, keywords)

        return node

    def parse(
        self,
        content: Union[str, List[str]],
        context: Optional["ParseContext"] = None,
        **kwargs: Any,
    ) -> "ParseResult":
        """統一パースメソッド - KeywordParserProtocol準拠"""
        try:
            # キャッシュ確認
            cache_key = create_cache_key(content, context, "parse")
            cached_result = self.cache.get_parse_cache(cache_key)
            if cached_result:
                return cached_result

            self._clear_errors_warnings()

            # 基本パース実行
            if isinstance(content, list):
                nodes = self._parse_content_lines(content)
            else:
                nodes = [self._parse_implementation(content)]

            # ParseResult作成
            result = create_parse_result(
                nodes=[n for n in nodes if n is not None],
                success=True,
                errors=self.get_errors(),
                warnings=self.get_warnings(),
                metadata={
                    "parser_type": "keyword",
                    "keyword_count": len(nodes) if nodes else 0,
                },
            )

            # キャッシュ保存
            self.cache.set_parse_cache(cache_key, result)
            return result

        except Exception as e:
            self.logger.error(f"Keyword parsing error: {e}")
            return create_parse_result(
                nodes=[],
                success=False,
                errors=[f"Keyword parsing failed: {e}"],
                warnings=[],
                metadata={"parser_type": "keyword"},
            )

    def _parse_content_lines(self, lines: List[str]) -> List["Node"]:
        """行リストから複数キーワードを解析"""
        nodes = []
        for line in lines:
            if line.strip():
                node = self._parse_implementation(line)
                if node:
                    nodes.append(node)
        return nodes

    def get_errors(self) -> List[str]:
        """エラー一覧取得"""
        return getattr(self, "_errors", [])

    def get_warnings(self) -> List[str]:
        """警告一覧取得"""
        return getattr(self, "_warnings", [])

    def validate(
        self, content: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """キーワード構文チェック"""
        return self.validator.validate(content, context)

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報（プロトコル準拠）"""
        return {
            "name": "UnifiedKeywordParser",
            "version": "3.0.0",
            "supported_formats": ["kumihan", "keyword", "markdown"],
            "capabilities": [
                "basic_keywords",
                "advanced_keywords",
                "custom_keywords",
                "attribute_parsing",
                "marker_parsing",
                "content_processing",
                "validation",
                "error_recovery",
                "performance_caching",
                "nested_structure",
            ],
            "parser_type": self.parser_type,
            "architecture": "分割最適化型",
        }

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定"""
        supported = {"kumihan", "keyword", "markdown"}
        return format_hint.lower() in supported

    # === KeywordParserProtocol実装 ===

    def parse_keywords(
        self, text: str, context: Optional["ParseContext"] = None
    ) -> List[str]:
        """テキストからキーワードを抽出（プロトコル準拠）"""
        keyword_info = self.keyword_extractor.extract_keyword_info(text)
        if keyword_info:
            return keyword_info["keywords"]
        return []

    def validate_keyword(
        self, keyword: str, context: Optional["ParseContext"] = None
    ) -> bool:
        """単一キーワードの妥当性チェック（プロトコル準拠）"""
        return self.validator.validate_keyword(keyword, context)

    def get_keyword_info(
        self, keyword: str, context: Optional["ParseContext"] = None
    ) -> Optional[Dict[str, Any]]:
        """キーワード情報を取得（プロトコル準拠）"""
        return self.info_processor.get_keyword_info(keyword, context)

    # === カスタムキーワード管理 ===

    def add_custom_keyword(self, keyword: str, handler: Any) -> None:
        """カスタムキーワード追加"""
        self.custom_handler.add_custom_keyword(keyword, handler)
        self.keyword_handlers[keyword] = handler

    def remove_custom_keyword(self, keyword: str) -> bool:
        """カスタムキーワード削除"""
        success = self.custom_handler.remove_custom_keyword(keyword)
        if success and keyword in self.keyword_handlers:
            del self.keyword_handlers[keyword]
        return success


# 後方互換性のためのエイリアス
KeywordParser = UnifiedKeywordParser
