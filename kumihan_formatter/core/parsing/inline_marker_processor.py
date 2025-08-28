"""Inline Marker Processor - インラインマーカー処理専用モジュール

core_marker_parser.py分割により抽出 (Phase3最適化)
インラインマーカー処理関連の機能をすべて統合
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from ...ast_nodes import Node, create_node, error_node
import logging


class InlineMarkerProcessor:
    """インラインマーカー処理専用クラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._initialize_patterns()

    def _initialize_patterns(self):
        """インラインマーカーパターンを初期化"""
        # インラインマーカー基本パターン
        self.inline_pattern = re.compile(r"(?:^|\s)([^\s#]+)#([^#\n]*?)#", re.MULTILINE)

        # 強調マーカーパターン
        self.emphasis_patterns = {
            "bold": re.compile(r"\*\*([^*]+)\*\*"),
            "italic": re.compile(r"\*([^*]+)\*"),
            "underline": re.compile(r"_([^_]+)_"),
            "strikethrough": re.compile(r"~~([^~]+)~~"),
            "code": re.compile(r"`([^`]+)`"),
        }

        # キーワード分離パターン
        self.keyword_separator = re.compile(r"[,\s]+")

        # 属性パターン
        self.attribute_pattern = re.compile(
            r'(\w+)[:=](["\']?)([^"\'\s]*)\2', re.IGNORECASE
        )

    def extract_inline_content(self, line: str, keywords: List[str]) -> str:
        """行からインラインコンテンツを抽出

        Args:
            line: 処理対象行
            keywords: 対象キーワードリスト

        Returns:
            抽出されたコンテンツ
        """
        if not line or not keywords:
            return ""

        # 各キーワードでコンテンツ抽出を試行
        for keyword in keywords:
            content = self._extract_content_for_keyword(line, keyword)
            if content:
                return content

        return ""

    def _extract_content_for_keyword(self, line: str, keyword: str) -> str:
        """特定キーワードでコンテンツを抽出"""
        # キーワード後の#区切りパターンを検索
        pattern = rf"{re.escape(keyword)}\s*#([^#]*?)#"
        match = re.search(pattern, line, re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # フォールバック: キーワード後のテキスト
        keyword_pos = line.lower().find(keyword.lower())
        if keyword_pos >= 0:
            after_keyword = line[keyword_pos + len(keyword) :].strip()
            # 最初の区切り文字まで
            for separator in ["#", "\n", "\t"]:
                if separator in after_keyword:
                    after_keyword = after_keyword.split(separator)[0]
            return after_keyword.strip()

        return ""

    def parse_inline_format(
        self, content: str, keyword: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[Node]:
        """インライン形式を解析

        Args:
            content: コンテンツ
            keyword: キーワード
            context: 解析コンテキスト

        Returns:
            解析結果ノードまたはNone
        """
        if not content or not keyword:
            return None

        context = context or {}

        # コンテンツの前処理
        processed_content = self._preprocess_inline_content(content)

        # 強調マーカーの処理
        processed_content = self._process_emphasis_markers(processed_content)

        # 属性の抽出
        attributes = self._extract_inline_attributes(processed_content)
        clean_content = self._remove_attributes_from_content(processed_content)

        # ノード作成
        node = create_node(keyword.lower(), clean_content)

        # 属性設定
        if attributes:
            node.attributes.update(attributes)

        # インライン形式フラグ
        node.attributes["format_type"] = "inline"
        node.attributes["original_keyword"] = keyword

        # コンテキスト情報追加
        if context:
            node.attributes["context"] = context

        self.logger.debug(f"インライン解析完了: {keyword} -> {len(clean_content)}文字")
        return node

    def _preprocess_inline_content(self, content: str) -> str:
        """インラインコンテンツを前処理"""
        # 前後の空白除去
        content = content.strip()

        # 連続する空白を単一に
        content = re.sub(r"\s+", " ", content)

        # エスケープシーケンス処理
        content = content.replace("\\#", "#")
        content = content.replace("\\*", "*")
        content = content.replace("\\_", "_")

        return content

    def _process_emphasis_markers(self, content: str) -> str:
        """強調マーカーを処理"""
        processed = content

        # 各強調パターンを処理
        for marker_type, pattern in self.emphasis_patterns.items():
            processed = pattern.sub(
                lambda m: f"<{marker_type}>{m.group(1)}</{marker_type}>", processed
            )

        return processed

    def _extract_inline_attributes(self, content: str) -> Dict[str, str]:
        """インラインコンテンツから属性を抽出"""
        attributes = {}

        for match in self.attribute_pattern.finditer(content):
            attr_name = match.group(1).lower()
            attr_value = match.group(3)
            attributes[attr_name] = attr_value

        return attributes

    def _remove_attributes_from_content(self, content: str) -> str:
        """コンテンツから属性を除去"""
        return self.attribute_pattern.sub("", content).strip()

    def create_node_for_keyword(self, keyword: str, content: str) -> Optional[Node]:
        """キーワードに対応するノードを作成

        Args:
            keyword: キーワード
            content: コンテンツ

        Returns:
            作成されたノードまたはNone
        """
        if not keyword:
            return None

        # キーワード正規化
        normalized_keyword = self._normalize_keyword(keyword)

        # ノード作成
        node = create_node(normalized_keyword, content)

        # メタデータ追加
        node.attributes["original_keyword"] = keyword
        node.attributes["processor"] = "inline_marker"

        return node

    def _normalize_keyword(self, keyword: str) -> str:
        """キーワードを正規化"""
        # 基本正規化
        normalized = keyword.strip().lower()

        # 日本語キーワードマッピング
        jp_mappings = {
            "太字": "bold",
            "ボールド": "bold",
            "イタリック": "italic",
            "斜体": "italic",
            "下線": "underline",
            "取消線": "strikethrough",
            "コード": "code",
            "強調": "emphasis",
            "マーク": "mark",
        }

        return jp_mappings.get(normalized, normalized)

    def find_matching_marker(
        self, text: str, start_pos: int = 0, marker_types: Optional[List[str]] = None
    ) -> Optional[Tuple[str, int, int]]:
        """マッチするマーカーを検索

        Args:
            text: 検索対象テキスト
            start_pos: 開始位置
            marker_types: 検索対象マーカータイプ

        Returns:
            (マーカータイプ, 開始位置, 終了位置)またはNone
        """
        marker_types = marker_types or list(self.emphasis_patterns.keys())

        earliest_match = None
        earliest_pos = len(text)

        # 各マーカータイプで検索
        for marker_type in marker_types:
            if marker_type in self.emphasis_patterns:
                pattern = self.emphasis_patterns[marker_type]
                match = pattern.search(text, start_pos)

                if match and match.start() < earliest_pos:
                    earliest_pos = match.start()
                    earliest_match = (marker_type, match.start(), match.end())

        # インラインパターンでも検索
        inline_match = self.inline_pattern.search(text, start_pos)
        if inline_match and inline_match.start() < earliest_pos:
            keyword = inline_match.group(1)
            earliest_match = ("inline", inline_match.start(), inline_match.end())

        return earliest_match

    def is_valid_marker_content(self, content: str) -> bool:
        """マーカーコンテンツが有効かチェック

        Args:
            content: チェック対象コンテンツ

        Returns:
            有効性
        """
        if not content or not content.strip():
            return False

        # 長さチェック
        if len(content) > 1000:
            return False

        # 不正文字チェック
        if re.search(r"[<>{}]", content):
            return False

        return True

    def process_line_markers(self, line: str) -> List[Node]:
        """行内のすべてのマーカーを処理

        Args:
            line: 処理対象行

        Returns:
            処理結果ノードのリスト
        """
        nodes = []
        pos = 0

        while pos < len(line):
            match = self.find_matching_marker(line, pos)
            if not match:
                break

            marker_type, start, end = match

            if marker_type == "inline":
                # インラインマーカー処理
                match_obj = self.inline_pattern.search(line, pos)
                if match_obj:
                    keyword = match_obj.group(1)
                    content = match_obj.group(2)

                    node = self.parse_inline_format(content, keyword)
                    if node:
                        nodes.append(node)
            else:
                # 強調マーカー処理
                pattern = self.emphasis_patterns[marker_type]
                match_obj = pattern.search(line, pos)
                if match_obj:
                    content = match_obj.group(1)
                    node = create_node(marker_type, content)
                    node.attributes["format_type"] = "emphasis"
                    nodes.append(node)

            pos = end

        return nodes
