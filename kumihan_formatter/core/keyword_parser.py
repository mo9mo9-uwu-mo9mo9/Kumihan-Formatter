"""Keyword parsing utilities for Kumihan-Formatter（分割後統合インポート）

This module handles the parsing and validation of Kumihan syntax keywords,
including compound keywords and error suggestions.

このファイルは技術的負債解消（Issue #476）により分割されました：
- keyword_parsing/definitions.py: キーワード定義
- keyword_parsing/marker_parser.py: マーカー解析
- keyword_parsing/validator.py: キーワード検証
"""

from typing import Any

from .ast_nodes import Node, NodeBuilder, error_node
from .keyword_parsing import KeywordDefinitions, KeywordValidator, MarkerParser


class KeywordParser:
    """
    Kumihan記法キーワードパーサー（記法解析の中核）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#ブロックキーワード→タグ対照表
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - NodeBuilder: ASTノード構築
    - Node: 生成するASTノード
    - error_node: エラー時のノード生成
    - Parser: このクラスを使用する上位パーサー

    責務:
    - Kumihan記法キーワードの解析
    - 複合キーワードの分解とネスト構造構築
    - ハイライト色属性など特殊属性の処理
    - 不正キーワードのエラー処理とサジェスト
    """

    # Default block keyword definitions
    DEFAULT_BLOCK_KEYWORDS = {
        "太字": {"tag": "strong"},
        "イタリック": {"tag": "em"},
        "枠線": {"tag": "div", "class": "box"},
        "ハイライト": {"tag": "div", "class": "highlight"},
        "見出し1": {"tag": "h1"},
        "見出し2": {"tag": "h2"},
        "見出し3": {"tag": "h3"},
        "見出し4": {"tag": "h4"},
        "見出し5": {"tag": "h5"},
        "折りたたみ": {"tag": "details", "summary": "詳細を表示"},
        "ネタバレ": {"tag": "details", "summary": "ネタバレを表示"},
    }

    # Keyword nesting order (outer to inner)
    NESTING_ORDER = [
        "details",  # 折りたたみ, ネタバレ
        "div",  # 枠線, ハイライト
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",  # 見出し
        "strong",  # 太字
        "em",  # イタリック
    ]

    def __init__(self, config: Any = None) -> None:
        """Initialize keyword parser with fixed keywords"""
        # 分割されたコンポーネントを初期化
        self.definitions = KeywordDefinitions(config)
        self.marker_parser = MarkerParser(self.definitions)
        self.validator = KeywordValidator(self.definitions)

        # 後方互換性のため既存プロパティを維持
        self.BLOCK_KEYWORDS = self.definitions.BLOCK_KEYWORDS

    def _normalize_marker_syntax(self, marker_content: str) -> str:
        """後方互換性のため分割されたコンポーネントに委譲"""
        return self.marker_parser.normalize_marker_syntax(marker_content)

    def parse_marker_keywords(
        self, marker_content: str
    ) -> tuple[list[str], dict[str, Any], list[str]]:
        """後方互換性のため分割されたコンポーネントに委譲"""
        return self.marker_parser.parse_marker_keywords(marker_content)

    def validate_keywords(self, keywords: list[str]) -> tuple[list[str], list[str]]:
        """後方互換性のため分割されたコンポーネントに委譲"""
        return self.validator.validate_keywords(keywords)

    def _get_keyword_suggestions(
        self, invalid_keyword: str, max_suggestions: int = 3
    ) -> list[str]:
        """後方互換性のため分割されたコンポーネントに委譲"""
        return self.validator.get_keyword_suggestions(invalid_keyword, max_suggestions)

    def create_single_block(
        self, keyword: str, content: str, attributes: dict[str, Any]
    ) -> Node:
        """Create a single block node from keyword"""
        if keyword not in self.BLOCK_KEYWORDS:
            return error_node(f"不明なキーワード: {keyword}")

        block_def = self.BLOCK_KEYWORDS[keyword]
        tag = block_def["tag"]

        # Parse content - for single blocks, use content directly if provided
        if content.strip():
            parsed_content = self._parse_block_content(content)
        else:
            parsed_content = [""]

        # Create node with appropriate builder
        builder = NodeBuilder(tag).content(parsed_content)

        # Add class if specified
        if "class" in block_def:
            builder.css_class(block_def["class"])

        # Add summary for details elements
        if "summary" in block_def:
            builder.attribute("summary", block_def["summary"])

        # Handle color attribute for highlight
        if keyword == "ハイライト" and "color" in attributes:
            color = attributes["color"]
            if not color.startswith("#"):
                color = "#" + color
            builder.style(f"background-color:{color}")

        # Add other attributes
        for key, value in attributes.items():
            if key not in ["color"]:  # Skip already handled attributes
                builder.attribute(key, value)

        return builder.build()

    def create_compound_block(
        self, keywords: list[str], content: str, attributes: dict[str, Any]
    ) -> Node:
        """Create nested block structure from compound keywords"""
        if not keywords:
            return error_node("キーワードが指定されていません")

        # Validate all keywords first
        valid_keywords, error_messages = self.validate_keywords(keywords)
        if error_messages:
            return error_node("; ".join(error_messages))

        # Sort keywords by nesting order
        sorted_keywords = self._sort_keywords_by_nesting_order(valid_keywords)

        # Build nested structure from outer to inner
        root_node = None
        current_node = None

        for i, keyword in enumerate(sorted_keywords):
            block_def = self.BLOCK_KEYWORDS[keyword]
            tag = block_def["tag"]

            # Create builder for this level
            builder = NodeBuilder(tag)

            # Add class if specified
            if "class" in block_def:
                builder.css_class(block_def["class"])

            # Add summary for details elements
            if "summary" in block_def:
                builder.attribute("summary", block_def["summary"])

            # Handle special attributes for the outermost element
            if i == 0:
                # Handle color attribute for highlight
                if keyword == "ハイライト" and "color" in attributes:
                    color = attributes["color"]
                    if not color.startswith("#"):
                        color = "#" + color
                    builder.style(f"background-color:{color}")

                # Add other attributes
                for key, value in attributes.items():
                    if key not in ["color"]:
                        builder.attribute(key, value)

            # Set content for the innermost element
            if i == len(sorted_keywords) - 1:
                parsed_content = self._parse_block_content(content)
                builder.content(parsed_content)
            else:
                # This will be set when we build the nested structure
                builder.content([""])

            # Build the node
            node = builder.build()

            if root_node is None:
                root_node = node
                current_node = node
            else:
                # Find the content and replace it with the new node
                if (
                    current_node
                    and hasattr(current_node, "content")
                    and current_node.content
                ):
                    current_node.content = [node]
                current_node = node

        return root_node or error_node("ノード作成に失敗しました")

    def _parse_block_content(self, content: str) -> list[Any]:
        """Parse block content, handling inline keywords"""
        if not content.strip():
            return [""]

        # Check for inline keywords in content
        processed_content = self._process_inline_keywords(content)
        return [processed_content]

    def _process_inline_keywords(self, content: str) -> str:
        """Process inline keywords within content"""
        # Simple inline processing - expand this as needed
        return content

    def _sort_keywords_by_nesting_order(self, keywords: list[str]) -> list[str]:
        """Sort keywords by their nesting order (outer to inner)"""
        # Map keywords to their tags
        keyword_tags = {}
        for keyword in keywords:
            if keyword in self.BLOCK_KEYWORDS:
                tag = self.BLOCK_KEYWORDS[keyword]["tag"]
                keyword_tags[keyword] = tag

        # Sort by nesting order
        def get_nesting_index(keyword: str) -> int:
            tag = keyword_tags.get(keyword)
            if tag in self.NESTING_ORDER:
                return self.NESTING_ORDER.index(tag)
            return len(self.NESTING_ORDER)  # Unknown tags go last

        return sorted(keywords, key=get_nesting_index)


