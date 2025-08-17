"""高度キーワード解析機能

高度なキーワード解析処理:
- 複合キーワード分割
- ルビ記法処理
- 高度な属性解析
- ネスト構造処理

Issue #914: アーキテクチャ最適化 - keyword_parser.py分割
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from ....ast_nodes import (
    Node,
    NodeBuilder,
    error_node,
)

# from ...base.parser_protocols import ParseContext, ParseResult


class AdvancedKeywordParser:
    """高度キーワード解析クラス

    高度なキーワード解析機能を提供:
    - 複合キーワード分割
    - ルビ記法処理
    - ネスト構造処理
    - 高度な属性解析
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """初期化

        Args:
            config: 設定辞書
        """
        self.config = config or {}
        self._setup_advanced_patterns()
        self._setup_nesting_order()
        self._setup_legacy_keywords()

    def _setup_advanced_patterns(self) -> None:
        """高度なパターンの設定"""
        self.advanced_patterns = {
            # ルビ記法パターン
            "ruby": re.compile(r"^ルビ\s+(.+)$"),
            # 複合キーワード記号
            "compound_separators": re.compile(r"[+＋\-－,，]"),
            # ネスト構造パターン
            "nested_block": re.compile(r"#([^#]+)#([^#]*)##"),
            # 属性指定パターン
            "attribute_block": re.compile(r"\[([^\]]+)\]"),
        }

    def _setup_nesting_order(self) -> None:
        """キーワードネスト順序の設定"""
        self.NESTING_ORDER = [
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

    def _setup_legacy_keywords(self) -> None:
        """レガシーキーワードの設定"""
        # DEFAULT_BLOCK_KEYWORDS の統合（後方互換性のため）
        self.DEFAULT_BLOCK_KEYWORDS = {
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

        # 後方互換性プロパティ
        self.BLOCK_KEYWORDS = self.DEFAULT_BLOCK_KEYWORDS

    def parse_marker_keywords(
        self, marker_content: str
    ) -> Tuple[List[str], Dict[str, Any], List[str]]:
        """マーカーからキーワードと属性を解析

        Args:
            marker_content: マーカーコンテンツ

        Returns:
            (キーワードリスト, 属性辞書, エラーリスト)
        """
        if not isinstance(marker_content, str):
            return [], {}, ["Invalid marker content type"]

        keywords: List[str] = []
        attributes: Dict[str, Any] = {}
        errors: List[str] = []

        marker_content = marker_content.strip()
        if not marker_content:
            return keywords, attributes, errors

        try:
            # ルビ記法の特別処理
            if marker_content.startswith("ルビ "):
                ruby_content = marker_content[3:].strip()
                ruby_result = self.parse_ruby_content(ruby_content)
                if ruby_result:
                    attributes["ruby"] = ruby_result
                    return keywords, attributes, errors

            # 複合キーワードの処理
            if "+" in marker_content or "＋" in marker_content:
                compound_keywords = self.split_compound_keywords(marker_content)
                for part in compound_keywords:
                    if part and self.is_valid_keyword(part):
                        keywords.append(part)
            else:
                # 単一キーワード
                keyword = marker_content.strip()
                if keyword and self.is_valid_keyword(keyword):
                    keywords.append(keyword)

        except Exception as e:
            errors.append(f"マーカー解析エラー: {str(e)}")

        return keywords, attributes, errors

    def split_compound_keywords(self, keyword_content: str) -> List[str]:
        """複合キーワードを個別のキーワードに分割

        Args:
            keyword_content: 分割対象のキーワード文字列

        Returns:
            個別キーワードのリスト
        """
        if not isinstance(keyword_content, str):
            return []

        keywords: List[str] = []

        # 複合キーワード記号での分割
        if "+" in keyword_content or "＋" in keyword_content:
            parts = re.split(r"[+＋]", keyword_content)
            for part in parts:
                part = part.strip()
                if part and self.is_valid_keyword(part):
                    keywords.append(part)
        else:
            # 単一キーワード
            keyword = keyword_content.strip()
            if keyword and self.is_valid_keyword(keyword):
                keywords.append(keyword)

        return keywords

    def parse_ruby_content(self, ruby_content: str) -> Optional[Dict[str, str]]:
        """ルビ記法の解析

        Args:
            ruby_content: ルビコンテンツ

        Returns:
            ルビ情報辞書、解析失敗時はNone
        """
        if not ruby_content:
            return None

        # ルビ記法: base|ruby 形式
        if "|" in ruby_content:
            parts = ruby_content.split("|", 1)
            if len(parts) == 2:
                return {"base": parts[0].strip(), "ruby": parts[1].strip()}

        # 単純なルビ
        return {"base": ruby_content, "ruby": ""}

    def create_ruby_node(self, text: str) -> Node:
        """ルビノードの作成

        Args:
            text: ルビテキスト

        Returns:
            ルビノード
        """
        ruby_info = self.parse_ruby_content(text)
        if ruby_info:
            return (
                NodeBuilder("ruby")
                .content(ruby_info["base"])
                .attribute("data-ruby", ruby_info["ruby"])
                .build()
            )
        else:
            return NodeBuilder("span").content(text).build()

    def create_compound_block(
        self, keywords: List[str], content: str, attributes: Dict[str, Any]
    ) -> Node:
        """複合ブロック構造の作成

        Args:
            keywords: キーワードリスト
            content: コンテンツ
            attributes: 属性辞書

        Returns:
            複合ブロックノード
        """
        if not keywords:
            return error_node("キーワードが指定されていません")

        # Sort keywords by nesting order
        sorted_keywords = self.sort_keywords_by_nesting_order(keywords)

        root_node = None
        current_node = None

        # Build nested structure from outer to inner
        for i, keyword in enumerate(sorted_keywords):
            if keyword not in self.BLOCK_KEYWORDS:
                return error_node(f"不明なキーワード: {keyword}")

            block_def = self.BLOCK_KEYWORDS[keyword]
            builder = NodeBuilder(block_def["tag"])

            # Add CSS class if specified
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
                    color = self.normalize_color_value(color)
                    builder.style(f"background-color:{color}")

                # Add other attributes
                for key, value in attributes.items():
                    if key not in ["color"]:
                        builder.attribute(key, value)

            # Set content for the innermost element
            if i == len(sorted_keywords) - 1:
                parsed_content = self.parse_block_content(content)
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

    def sort_keywords_by_nesting_order(self, keywords: List[str]) -> List[str]:
        """ネスト順序でキーワードをソート

        Args:
            keywords: ソート対象のキーワードリスト

        Returns:
            ソート済みキーワードリスト
        """
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
            return 999  # 不明なタグは最後に

        return sorted(keywords, key=get_nesting_index)

    def parse_block_content(self, content: str) -> List[Any]:
        """ブロックコンテンツの解析

        Args:
            content: 解析対象のコンテンツ

        Returns:
            解析済みコンテンツリスト
        """
        if not content.strip():
            return [""]

        # ブロックコンテンツの解析を実装
        return [content]

    def normalize_color_value(self, color: str) -> str:
        """色値を正規化

        Args:
            color: 正規化対象の色値

        Returns:
            正規化済み色値
        """
        # 既に16進数形式の場合はそのまま返す
        if color.startswith("#"):
            return color

        # その他の場合はそのまま返す（将来の拡張のため）
        return color

    def normalize_marker_syntax(self, marker_content: str) -> str:
        """マーカー記法の正規化

        Args:
            marker_content: 正規化対象のマーカー

        Returns:
            正規化済みマーカー
        """
        if not marker_content:
            return ""

        # 記号の正規化
        marker_content = marker_content.replace("＋", "+")
        marker_content = marker_content.replace("－", "-")

        return marker_content.strip()

    def is_valid_keyword(self, keyword: str) -> bool:
        """キーワードの有効性チェック

        Args:
            keyword: チェック対象のキーワード

        Returns:
            有効な場合True
        """
        if not keyword or not isinstance(keyword, str):
            return False

        keyword = keyword.strip()

        # デフォルトキーワードまたはレガシーキーワードに存在するか
        return keyword in self.DEFAULT_BLOCK_KEYWORDS

    def extract_nested_keywords(self, text: str) -> List[Dict[str, Any]]:
        """ネストしたキーワード構造を抽出

        Args:
            text: 解析対象のテキスト

        Returns:
            ネストキーワード情報のリスト
        """
        nested_keywords = []

        # ネストしたブロック記法を検出
        pattern = r"#([^#]+)#([^#]*)##"
        matches = re.finditer(pattern, text)

        for match in matches:
            keyword_text = match.group(1).strip()
            content = match.group(2).strip()

            # 複合キーワードの分割
            keywords = self.split_compound_keywords(keyword_text)

            if keywords:
                nested_info = {
                    "keywords": keywords,
                    "content": content,
                    "position": match.span(),
                    "original": match.group(0),
                }
                nested_keywords.append(nested_info)

        return nested_keywords
