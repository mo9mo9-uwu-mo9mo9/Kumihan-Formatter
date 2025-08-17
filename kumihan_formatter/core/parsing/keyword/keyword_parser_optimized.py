"""統合キーワードパーサー - 最適化版

Issue #914: アーキテクチャ最適化リファクタリング
元のkeyword_parser.py (886行) を機能別に分割し、統合制御機能として最適化

分割構造:
- keyword_parser.py (本ファイル): 統合制御・公開API
- parsers/basic_parser.py: 基本キーワード解析
- parsers/advanced_parser.py: 高度キーワード解析
- parsers/custom_parser.py: カスタムキーワード解析

既存API完全互換性維持、機能100%保持
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from ....ast_nodes import (
    Node,
    NodeBuilder,
    create_node,
    error_node,
)
from ...base import CompositeMixin, UnifiedParserBase
from ...base.parser_protocols import (
    KeywordParserProtocol,
    ParseContext,
    ParseResult,
    create_parse_result,
)
from ..protocols import ParserType
from .parsers.advanced_parser import AdvancedKeywordParser

# 分割されたパーサーをインポート
from .parsers.basic_parser import BasicKeywordParser
from .parsers.custom_parser import CustomKeywordParser


class UnifiedKeywordParser(UnifiedParserBase, CompositeMixin, KeywordParserProtocol):
    """統一キーワードパーサー - 最適化版

    分割されたパーサーを統合し、既存API完全互換性を維持:
    - BasicKeywordParser: 基本キーワード解析
    - AdvancedKeywordParser: 高度キーワード解析
    - CustomKeywordParser: カスタムキーワード解析

    機能:
    - キーワード定義・検証
    - マーカー解析・属性解析
    - 複合キーワード分割・ネスト構造構築
    - ルビ記法・インライン記法処理
    - 後方互換性維持
    """

    def __init__(self) -> None:
        super().__init__(parser_type=ParserType.KEYWORD)

        # 分割されたパーサーを初期化
        self.basic_parser = BasicKeywordParser(
            self.config if hasattr(self, "config") else {}
        )
        self.advanced_parser = AdvancedKeywordParser(
            self.config if hasattr(self, "config") else {}
        )
        self.custom_parser = CustomKeywordParser(
            self.config if hasattr(self, "config") else {}
        )

        # 統合機能の設定
        self._setup_unified_properties()
        self._setup_legacy_compatibility()

    def _setup_unified_properties(self) -> None:
        """統合プロパティの設定"""
        # 各パーサーのプロパティを統合
        self.default_keywords = self.basic_parser.default_keywords
        self.custom_keywords = self.custom_parser.custom_keywords
        self.deprecated_keywords = self.custom_parser.deprecated_keywords

        # レガシー互換性のためのプロパティ
        self.DEFAULT_BLOCK_KEYWORDS = self.advanced_parser.DEFAULT_BLOCK_KEYWORDS
        self.BLOCK_KEYWORDS = self.advanced_parser.BLOCK_KEYWORDS
        self.NESTING_ORDER = self.advanced_parser.NESTING_ORDER

    def _setup_legacy_compatibility(self) -> None:
        """レガシー互換性の設定"""
        # 統合機能: core/keyword_parser.py からの機能
        try:
            from ....keyword import KeywordDefinitions, KeywordValidator, MarkerParser

            # 分割されたコンポーネントを初期化（後方互換性のため）
            self.definitions = KeywordDefinitions(None)
            self.marker_parser = MarkerParser(self.definitions)
            self.validator = KeywordValidator(self.definitions)
        except Exception:
            # フォールバック：基本的な実装を使用
            self.definitions = None
            self.marker_parser = None
            self.validator = None

    def can_parse(self, content: Union[str, List[str]]) -> bool:
        """キーワード記法の解析可能性を判定"""
        if not super().can_parse(content):
            return False

        text = content if isinstance(content, str) else "\n".join(content)

        # Kumihanキーワード記法の特徴を検出
        return self._contains_keywords(text)

    def _contains_keywords(self, text: str) -> bool:
        """既知のキーワードが含まれているかチェック"""
        all_keywords = set(self.default_keywords.keys()) | set(
            self.custom_keywords.keys()
        )

        for keyword in all_keywords:
            if keyword in text:
                return True

        # パターンベースの検出
        if re.search(r"#[^#]+#[^#]*##", text):
            return True

        return False

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Node:
        """キーワード解析の実装"""
        self._start_timer("keyword_parsing")

        try:
            text = content if isinstance(content, str) else "\n".join(content)

            # 解析結果を格納するノード
            root_node = create_node("keyword_document", content=text)

            # テキスト内のキーワードを解析
            keywords_found = self._extract_all_keywords(text)

            for keyword_info in keywords_found:
                keyword_node = self.basic_parser.create_keyword_node(keyword_info)
                root_node.children.append(keyword_node)

            self._end_timer("keyword_parsing")
            return root_node

        except Exception as e:
            self.add_error(f"キーワード解析エラー: {str(e)}")
            return create_node("error", content=f"Keyword parse error: {e}")

    def _extract_all_keywords(self, text: str) -> List[Dict[str, Any]]:
        """テキストからすべてのキーワードを抽出"""
        keywords_found = []

        # ブロック内キーワードの抽出
        block_matches = re.finditer(r"#([^#]+)#([^#]*)##", text)
        for match in block_matches:
            keyword_text = match.group(1).strip()
            content = match.group(2).strip()

            keyword_info = self.basic_parser.parse_keyword_string(keyword_text)
            keyword_info.update(
                {"content": content, "position": match.span(), "context": "block"}
            )
            keywords_found.append(keyword_info)

        return keywords_found

    # ==========================================
    # 委譲メソッド群（既存API互換性維持）
    # ==========================================

    def register_keyword(self, keyword: str, definition: Dict[str, Any]) -> None:
        """カスタムキーワードを登録"""
        self.custom_parser.register_keyword(keyword, definition)
        self.logger.info(f"Registered custom keyword: {keyword}")

    def unregister_keyword(self, keyword: str) -> bool:
        """カスタムキーワードの登録解除"""
        result = self.custom_parser.unregister_keyword(keyword)
        if result:
            self.logger.info(f"Unregistered custom keyword: {keyword}")
        return result

    def deprecate_keyword(self, keyword: str) -> None:
        """キーワードを非推奨にマーク"""
        self.custom_parser.deprecate_keyword(keyword)
        self.logger.warning(f"Keyword marked as deprecated: {keyword}")

    def get_keyword_suggestions(self, partial: str) -> List[str]:
        """部分文字列にマッチするキーワード候補を取得"""
        basic_suggestions = [
            kw for kw in self.default_keywords.keys() if partial.lower() in kw.lower()
        ]
        custom_suggestions = self.custom_parser.get_keyword_suggestions(partial)
        return sorted(set(basic_suggestions + custom_suggestions))

    def validate_keyword(self, keyword: str) -> Dict[str, Any]:
        """キーワードの妥当性を検証"""
        # 基本キーワードを先にチェック
        definition = self.basic_parser.get_keyword_definition(keyword)
        if definition:
            return {
                "valid": True,
                "type": definition.get("type"),
                "definition": definition,
                "deprecated": keyword in self.deprecated_keywords,
                "suggestions": [],
            }

        # カスタムキーワードをチェック
        return self.custom_parser.validate_keyword(keyword)

    def parse_marker_keywords(
        self, marker_content: str
    ) -> Tuple[List[str], Dict[str, Any], List[str]]:
        """マーカーからキーワードと属性を解析"""
        return self.advanced_parser.parse_marker_keywords(marker_content)

    def split_compound_keywords(self, keyword_content: str) -> List[str]:
        """複合キーワードを個別のキーワードに分割"""
        return self.advanced_parser.split_compound_keywords(keyword_content)

    def parse_keywords(self, content: str) -> List[str]:
        """コンテンツからキーワードを抽出"""
        if not content:
            return []

        keywords = []

        # ブロック記法からのキーワード抽出
        block_matches = re.finditer(r"#([^#]+)#[^#]*##", content)
        for match in block_matches:
            keyword_text = match.group(1).strip()
            if self._is_valid_keyword(keyword_text):
                keywords.append(keyword_text)

        return keywords

    def _is_valid_keyword(self, keyword: str) -> bool:
        """キーワードの有効性チェック"""
        return self.basic_parser.is_valid_keyword(
            keyword
        ) or self.advanced_parser.is_valid_keyword(keyword)

    def create_single_block(
        self, keyword: str, content: str, attributes: Dict[str, Any]
    ) -> Node:
        """単一ブロックノードの作成"""
        if keyword not in self.BLOCK_KEYWORDS:
            return error_node(f"不明なキーワード: {keyword}")

        # Create builder for the block
        builder = NodeBuilder(node_type=self.BLOCK_KEYWORDS[keyword]["tag"]).content(
            content
        )

        # Add attributes if provided
        if attributes:
            for key, value in attributes.items():
                builder.attribute(key, value)

        return builder.build()

    def create_compound_block(
        self, keywords: List[str], content: str, attributes: Dict[str, Any]
    ) -> Node:
        """複合ブロック構造の作成"""
        return self.advanced_parser.create_compound_block(keywords, content, attributes)

    def get_keyword_statistics(self) -> Dict[str, Any]:
        """キーワード統計情報を取得"""
        stats = self._get_performance_stats()
        basic_stats = {
            "default_keywords": len(self.default_keywords),
            "parser_type": self.parser_type,
        }
        custom_stats = self.custom_parser.get_custom_keyword_statistics()

        stats.update(basic_stats)
        stats.update(custom_stats)
        stats["total_keywords"] = (
            stats["default_keywords"]
            + stats["custom_keywords"]
            + stats["extension_keywords"]
        )

        return stats

    # ==========================================
    # プロトコル準拠メソッド（KeywordParserProtocol実装）
    # ==========================================

    def parse(
        self, content: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """統一パースインターフェース（プロトコル準拠）"""
        try:
            # 既存の parse_keywords ロジックを活用
            keywords = self.parse_keywords(content)
            nodes = [self._create_keyword_node_from_text(kw) for kw in keywords]
            return create_parse_result(nodes=nodes, success=True)
        except Exception as e:
            result = create_parse_result(success=False)
            result.add_error(f"キーワードパース失敗: {e}")
            return result

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """バリデーション実装（プロトコル準拠）"""
        errors = []
        try:
            keywords = self.parse_keywords(content)
            for keyword in keywords:
                validation_result = self.validate_keyword(keyword)
                if not validation_result["valid"]:
                    errors.append(f"無効なキーワード: {keyword}")
        except Exception as e:
            errors.append(f"バリデーションエラー: {e}")
        return errors

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報（プロトコル準拠）"""
        return {
            "name": "UnifiedKeywordParser",
            "version": "2.1.0",
            "supported_formats": ["kumihan", "keyword"],
            "capabilities": ["keyword_extraction", "attribute_parsing"],
            "parser_type": self.parser_type,
            "architecture": "分割統合型",
        }

    def supports_format(self, format_hint: str) -> bool:
        """フォーマット対応判定（プロトコル準拠）"""
        return format_hint in ["kumihan", "keyword", "text"]

    def _create_keyword_node_from_text(self, keyword: str) -> Node:
        """テキストからキーワードノードを作成"""
        return create_node("keyword", content=keyword, metadata={"keyword": keyword})

    # ==========================================
    # レガシー互換性メソッド
    # ==========================================

    def parse_new_format(self, line: str) -> Dict[str, Any]:
        """新形式マーカーの解析（後方互換用）"""
        return {"keywords": [], "content": line, "attributes": {}}

    def get_node_factory(self, keywords: Union[str, Tuple[Any, ...]]) -> Any:
        """ノードファクトリーの取得（後方互換用）"""
        return NodeBuilder(node_type="div")

    def parse_legacy(self, text: str) -> List[Node]:
        """レガシーparse メソッドのエイリアス"""
        result = self._parse_implementation(text)
        return [result] if isinstance(result, Node) else result
