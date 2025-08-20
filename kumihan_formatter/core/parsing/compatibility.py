"""後方互換性レイヤー

Issue #880 Phase 2C: 既存パーサーから新統一パーサーへの移行支援
段階的非推奨化とスムーズな移行を提供
"""

import warnings
from typing import Any, Dict, List, Optional, Union

from ..ast_nodes import Node
from ..utilities.logger import get_logger
from .coordinator import get_global_coordinator, register_default_parsers


class LegacyParserWrapper:
    """レガシーパーサーラッパー基底クラス

    既存パーサーのインターフェースを維持しつつ
    内部的には新統一パーサーシステムを使用
    """

    def __init__(self, parser_type: str, original_class_name: str):
        self.parser_type = parser_type
        self.original_class_name = original_class_name
        self.logger = get_logger(f"Legacy{original_class_name}")

        # 初回のみデフォルトパーサーを登録
        self._ensure_default_parsers()

        # 非推奨警告の表示
        self._show_deprecation_warning()

    def _ensure_default_parsers(self) -> None:
        """デフォルトパーサーが登録されていることを確認"""
        coordinator = get_global_coordinator()
        if not coordinator.get_registered_parsers():
            register_default_parsers()

    def _show_deprecation_warning(self) -> None:
        """非推奨警告の表示"""
        warnings.warn(
            f"{self.original_class_name} is deprecated and will be removed in a future version. "
            f"Use kumihan_formatter.core.parsing.UnifiedParsingCoordinator instead.",
            DeprecationWarning,
            stacklevel=3,
        )

    def parse(self, content: Union[str, List[str]], **kwargs: Any) -> Node:
        """統一パーサーシステム経由で解析"""
        coordinator = get_global_coordinator()
        result = coordinator.parse(content, parser_type=self.parser_type, **kwargs)
        return result.node


class LegacyBlockParser(LegacyParserWrapper):
    """BlockParser後方互換ラッパー"""

    def __init__(self, keyword_parser: Optional[Any] = None):
        super().__init__("block", "BlockParser")
        self.keyword_parser = keyword_parser  # 互換性のため保持

    def parse_block(self, content: str, **kwargs: Any) -> Node:
        """ブロック解析（レガシーメソッド）"""
        return self.parse(content, **kwargs)

    def validate_block(self, content: str) -> bool:
        """ブロック検証（レガシーメソッド）"""
        coordinator = get_global_coordinator()
        parsers = coordinator.get_registered_parsers()
        if "block" in parsers:
            block_parser = coordinator._parsers["block"]
            return block_parser.can_parse(content)
        return False


class LegacyKeywordParser(LegacyParserWrapper):
    """KeywordParser後方互換ラッパー"""

    def __init__(self) -> None:
        super().__init__("keyword", "KeywordParser")

    def parse_keywords(self, content: str, **kwargs: Any) -> Node:
        """キーワード解析（レガシーメソッド）"""
        return self.parse(content, **kwargs)

    def validate_keyword(self, keyword: str) -> bool:
        """キーワード検証（レガシーメソッド）"""
        coordinator = get_global_coordinator()
        parsers = coordinator.get_registered_parsers()
        if "keyword" in parsers:
            keyword_parser = coordinator._parsers["keyword"]
            if hasattr(keyword_parser, "validate_keyword"):
                result = keyword_parser.validate_keyword(keyword)
                return result.get("valid", False)
        return False


class LegacyListParser(LegacyParserWrapper):
    """ListParser後方互換ラッパー"""

    def __init__(self) -> None:
        super().__init__("list", "ListParser")

    def parse_list(self, content: Union[str, List[str]], **kwargs: Any) -> Node:
        """リスト解析（レガシーメソッド）"""
        return self.parse(content, **kwargs)

    def parse_nested_list(self, content: Union[str, List[str]], **kwargs: Any) -> Node:
        """ネストリスト解析（レガシーメソッド）"""
        # 新パーサーは自動的にネスト対応
        return self.parse(content, **kwargs)


class LegacyMarkdownParser(LegacyParserWrapper):
    """MarkdownParser後方互換ラッパー"""

    def __init__(self) -> None:
        super().__init__("markdown", "MarkdownParser")

    def parse_markdown(self, content: str, **kwargs: Any) -> Node:
        """Markdown解析（レガシーメソッド）"""
        return self.parse(content, **kwargs)

    def convert_to_html(self, content: str, **kwargs: Any) -> str:
        """HTML変換（レガシーメソッド）"""
        # 簡単な実装（実際のHTML変換は別途実装が必要）
        node = self.parse(content, **kwargs)
        return f"<div>{node.content}</div>"


class LegacySpecialBlockParser(LegacyParserWrapper):
    """SpecialBlockParser後方互換ラッパー"""

    def __init__(self) -> None:
        super().__init__("block", "SpecialBlockParser")

    def parse_special_block(self, content: str, block_type: str, **kwargs: Any) -> Node:
        """特殊ブロック解析（レガシーメソッド）"""
        # 特殊ブロックタイプを属性として渡す
        kwargs["block_type"] = block_type
        return self.parse(content, **kwargs)


class LegacyParsingCoordinator(LegacyParserWrapper):
    """ParsingCoordinator後方互換ラッパー"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("content", "ParsingCoordinator")
        self.config = config or {}

    def parse_document(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Dict[str, Any]:
        """文書解析（レガシーメソッド）"""
        coordinator = get_global_coordinator()
        result = coordinator.parse_with_fallback(content, **kwargs)

        # レガシー形式のレスポンス
        return {
            "content": result.node,
            "parser_type": result.parser_type,
            "metadata": result.metadata,
            "success": result.is_successful(),
            "errors": result.errors,
            "warnings": result.warnings,
        }

    def select_best_parser(self, content: Union[str, List[str]]) -> str:
        """最適パーサー選択（レガシーメソッド）"""
        coordinator = get_global_coordinator()
        parser = coordinator.select_parser(content)
        return parser.get_parser_type() if parser else "unknown"


# モジュールレベルの互換関数


def create_block_parser(**kwargs: Any) -> LegacyBlockParser:
    """BlockParser作成関数（レガシー互換）"""
    return LegacyBlockParser(**kwargs)


def create_keyword_parser(**kwargs: Any) -> LegacyKeywordParser:
    """KeywordParser作成関数（レガシー互換）"""
    return LegacyKeywordParser()


def create_list_parser(**kwargs: Any) -> LegacyListParser:
    """ListParser作成関数（レガシー互換）"""
    return LegacyListParser()


def create_markdown_parser(**kwargs: Any) -> LegacyMarkdownParser:
    """MarkdownParser作成関数（レガシー互換）"""
    return LegacyMarkdownParser()


def create_parsing_coordinator(**kwargs: Any) -> LegacyParsingCoordinator:
    """ParsingCoordinator作成関数（レガシー互換）"""
    return LegacyParsingCoordinator(**kwargs)


# レガシーインポートのエイリアス

# Issue #880: これらのエイリアスは Phase 3 で段階的に削除予定
BlockParser = LegacyBlockParser
KeywordParser = LegacyKeywordParser
ListParser = LegacyListParser
MarkdownParser = LegacyMarkdownParser
SpecialBlockParser = LegacySpecialBlockParser
ParsingCoordinator = LegacyParsingCoordinator


def show_migration_guide() -> None:
    """移行ガイドの表示"""
    guide = """
=== Kumihan-Formatter パーサー移行ガイド ===

新しい統一パーサーシステムへの移行をお願いします:

【旧システム】
from kumihan_formatter.core.parsing.block import BlockParser
from kumihan_formatter.core.parsing.keyword.keyword_parser import KeywordParser

【新システム】
from kumihan_formatter.core.parsing import (
    UnifiedParsingCoordinator,
    get_global_coordinator,
    register_default_parsers
)

# 統一パーサーの使用例:
coordinator = get_global_coordinator()
register_default_parsers()
result = coordinator.parse(content)

詳細: docs/migration/parser-migration.md
"""
    print(guide)


def check_compatibility_status() -> Dict[str, Any]:
    """互換性状況のチェック"""
    coordinator = get_global_coordinator()
    stats = coordinator.get_statistics()

    return {
        "registered_parsers": stats.get("registered_parsers", 0),
        "legacy_wrappers_active": True,
        "migration_required": True,
        "deprecation_warnings": True,
        "recommended_action": "migrate_to_unified_parsing",
        "migration_guide": "Use show_migration_guide() for detailed instructions",
    }
