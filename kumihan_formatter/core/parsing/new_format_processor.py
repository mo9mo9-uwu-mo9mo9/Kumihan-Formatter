"""New Format Processor - 新記法処理専用モジュール

core_marker_parser.py分割により抽出 (Phase3最適化)
新記法処理関連の機能をすべて統合
"""

import re
from typing import Dict, List, Optional, Tuple

from ..ast_nodes import Node, create_node, error_node
import logging

if TYPE_CHECKING:
    from .protocols import ParseResult


class NewFormatProcessor:
    """新記法処理専用クラス"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._initialize_patterns()

    def _initialize_patterns(self) -> None:
        """新記法パターンを初期化"""
        # 新記法のパターン定義
        self.new_format_pattern = re.compile(
            r"# (?P<keyword>[^#]+) #(?P<content>[^#]*)##", re.MULTILINE | re.DOTALL
        )

        # 複合キーワードパターン
        self.compound_keyword_pattern = re.compile(r"[,+&]")

        # 属性パターン
        self.attribute_pattern = re.compile(r'(\w+)=(["\']?)([^"\'\s]*)\2')

        # 色属性パターン
        self.color_pattern = re.compile(r"(?:color|色)[:=]\s*([#\w]+)", re.IGNORECASE)

    def parse_new_format_marker(
        self, text: str, start_index: int = 0
    ) -> Optional["ParseResult"]:
        """新記法マーカーを解析

        Args:
            text: 解析対象テキスト
            start_index: 開始位置

        Returns:
            解析結果またはNone
        """
        match = self.new_format_pattern.search(text, start_index)
        if not match:
            return None

        keyword = match.group("keyword").strip()
        content = match.group("content").strip() if match.group("content") else ""

        # バリデーション
        if not self._validate_new_format_syntax(keyword, content):
            return None

        # 複合キーワードの処理
        keywords = self.split_compound_keywords(keyword)

        # 主要キーワード選択
        primary_keyword = keywords[0] if keywords else keyword

        # ノード作成
        node = create_node(primary_keyword.lower(), content)

        # 複合キーワード属性追加
        if len(keywords) > 1:
            if node.attributes is not None:
                node.attributes["compound_keywords"] = keywords[1:]

        # 色属性処理
        color_content, remaining_content = self.extract_color_attribute(content)
        if color_content:
            if node.attributes is not None:
                node.attributes["color"] = color_content
            node.content = remaining_content

        # 結果構築
        from .protocols import ParseResult

        result = ParseResult(
            node=node,
            parser_type="new_format",
            metadata={
                "consumed_length": match.end() - match.start(),
                "start_position": match.start(),
                "end_position": match.end(),
            },
        )

        self.logger.debug(f"新記法解析成功: {keyword} -> {primary_keyword}")
        return result

    def _validate_new_format_syntax(self, keyword: str, content: str) -> bool:
        """新記法構文をバリデーション

        Args:
            keyword: キーワード部分
            content: コンテンツ部分

        Returns:
            有効性
        """
        # キーワードの基本チェック
        if not keyword or not keyword.strip():
            return False

        # 不正文字チェック
        if re.search(r"[<>{}]", keyword):
            return False

        # キーワード長制限
        if len(keyword) > 50:
            return False

        # コンテンツ長制限（オプショナル）
        if len(content) > 10000:
            self.logger.warning(f"コンテンツが長すぎます: {len(content)}文字")

        return True

    def parse_new_marker_format(self, text: str) -> List[Tuple[str, str, int, int]]:
        """新マーカー形式をすべて解析

        Args:
            text: 解析対象テキスト

        Returns:
            (キーワード, コンテンツ, 開始位置, 終了位置)のリスト
        """
        results = []

        for match in self.new_format_pattern.finditer(text):
            keyword = match.group("keyword").strip()
            content = match.group("content").strip() if match.group("content") else ""

            if self._validate_new_format_syntax(keyword, content):
                results.append((keyword, content, match.start(), match.end()))

        return results

    def extract_color_attribute(self, content: str) -> Tuple[str, str]:
        """コンテンツから色属性を抽出

        Args:
            content: 元のコンテンツ

        Returns:
            (色属性, 残りのコンテンツ)のタプル
        """
        color_match = self.color_pattern.search(content)

        if color_match:
            color_value = color_match.group(1)
            # 色属性を除去したコンテンツ
            remaining_content = self.color_pattern.sub("", content).strip()
            return color_value, remaining_content

        return "", content

    def split_compound_keywords(self, keyword_content: str) -> List[str]:
        """複合キーワードを分割

        Args:
            keyword_content: キーワード文字列

        Returns:
            分割されたキーワードのリスト
        """
        if not self.compound_keyword_pattern.search(keyword_content):
            return [keyword_content.strip()]

        # 分割文字に基づいて分割
        keywords = []
        for separator in [",", "+", "&"]:
            if separator in keyword_content:
                parts = keyword_content.split(separator)
                keywords.extend([part.strip() for part in parts if part.strip()])
                break

        # 重複除去と順序維持
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords if unique_keywords else [keyword_content.strip()]

    def parse_marker_keywords(self, keyword_string: str) -> List[str]:
        """マーカーキーワード文字列を解析

        Args:
            keyword_string: キーワード文字列

        Returns:
            解析されたキーワードのリスト
        """
        # 基本的な前処理
        cleaned = keyword_string.strip()
        if not cleaned:
            return []

        # 複合キーワード処理
        keywords = self.split_compound_keywords(cleaned)

        # キーワード正規化
        normalized_keywords = []
        for kw in keywords:
            normalized = self._normalize_keyword(kw)
            if normalized:
                normalized_keywords.append(normalized)

        return normalized_keywords

    def _normalize_keyword(self, keyword: str) -> str:
        """キーワードを正規化

        Args:
            keyword: 元のキーワード

        Returns:
            正規化されたキーワード
        """
        # 前後の空白除去
        normalized = keyword.strip()

        # 日本語キーワードマッピング
        jp_mappings = {
            "太字": "bold",
            "イタリック": "italic",
            "見出し": "heading",
            "脚注": "footnote",
            "リンク": "link",
            "画像": "image",
            "引用": "quote",
            "コード": "code",
        }

        # マッピングが存在すれば適用
        return jp_mappings.get(normalized, normalized.lower())

    def create_new_format_node(
        self, keyword: str, content: str, attributes: Optional[Dict[str, Any]] = None
    ) -> Node:
        """新記法用のノードを作成

        Args:
            keyword: キーワード
            content: コンテンツ
            attributes: 追加属性

        Returns:
            作成されたノード
        """
        # ノード作成
        node = create_node(keyword.lower(), content)

        # 属性追加
        if attributes is not None and node.attributes is not None:
            node.attributes.update(attributes)

        # 新記法フラグ
        if node.attributes is not None:
            node.attributes["format_type"] = "new_format"
            node.attributes["original_keyword"] = keyword

        return node

    def is_new_format_marker(self, text: str) -> bool:
        """テキストが新記法マーカーかどうか判定

        Args:
            text: 判定対象テキスト

        Returns:
            新記法マーカーかどうか
        """
        return self.new_format_pattern.search(text) is not None
