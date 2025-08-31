"""Specialized Parser - 特殊化パーサー統合モジュール

Issue #1252対応: 特殊処理系パーサーの統合
以下のコンポーネントを統合:
- CoreMarkerParser (マーカー解析)
- NewFormatProcessor (新フォーマット処理)
- RubyFormatProcessor (ルビフォーマット処理)
- InlineMarkerProcessor (インライン処理)

統合により重複処理を排除し、特殊化された解析機能を統一インターフェースで提供
"""

import re
import warnings
from typing import Any, Dict, List, Optional, Tuple, Union

from ..core.ast_nodes import Node, error_node
from ..core.utilities.logger import get_logger
from .keyword_definitions import KeywordDefinitions
from .unified_keyword_parser import UnifiedKeywordParser


# エラークラスは共通モジュールから使用
from kumihan_formatter.core.common.processing_errors import SpecializedParsingError


class SpecializedParser:
    """統合特殊化パーサー

    Issue #1252対応:
    - マーカーパーサー機能統合
    - 各種フォーマットプロセッサー統合
    - インライン処理統合
    - エラーハンドリング統一
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """SpecializedParser初期化

        Args:
            config: パーサー設定辞書
        """
        self.config = config or {}
        self.logger = get_logger(__name__)

        # コンポーネント初期化
        self._initialize_components()
        self._initialize_patterns()

    def _initialize_components(self) -> None:
        """コンポーネント初期化"""
        try:
            # キーワード定義とパーサー
            self.definitions = KeywordDefinitions()
            self.keyword_parser = UnifiedKeywordParser()

            # 各種プロセッサー（統合）
            self._new_format_patterns = self._init_new_format_patterns()
            self._ruby_format_patterns = self._init_ruby_format_patterns()
            self._inline_patterns = self._init_inline_patterns()

        except Exception as e:
            self.logger.error(f"コンポーネント初期化エラー: {e}")
            raise SpecializedParsingError(f"Component initialization failed: {e}")

    def _initialize_patterns(self) -> None:
        """パターン初期化"""
        # マーカーパターン（CoreMarkerParserから統合）
        self.marker_pattern = re.compile(r"#\s*([^#]+?)\s*#([^#]+?)##")

        # 新フォーマットパターン
        self.new_format_pattern = re.compile(r"\{\{([^}]+?)\}\}")

        # ルビフォーマットパターン
        self.ruby_pattern = re.compile(r"\|([^|]+?)\|([^|]*?)\|")

        # インラインパターン
        self.inline_pattern = re.compile(r"`([^`]+?)`")

    def parse(self, content: str) -> Node:
        """メイン解析処理

        Args:
            content: 解析対象コンテンツ

        Returns:
            解析結果ノード
        """
        if not content:
            return error_node("Empty content provided")

        try:
            # マーカー解析を最優先
            if self.marker_pattern.search(content):
                return self.parse_marker_content(content)

            # 新フォーマット解析
            elif self.new_format_pattern.search(content):
                return self.parse_new_format_content(content)

            # ルビフォーマット解析
            elif self.ruby_pattern.search(content):
                return self.parse_ruby_content(content)

            # インライン解析
            elif self.inline_pattern.search(content):
                return self.parse_inline_content(content)

            # 該当しない場合
            else:
                return self.parse_generic_special(content)

        except Exception as e:
            self.logger.error(f"特殊化パース処理エラー: {e}")
            return error_node(f"Specialized parsing error: {e}")

    def parse_marker_content(self, content: str) -> Node:
        """マーカーコンテンツ解析（CoreMarkerParser統合）

        Args:
            content: マーカーコンテンツ

        Returns:
            解析結果ノード
        """
        try:
            match = self.marker_pattern.search(content)
            if not match:
                return error_node("No valid marker pattern found")

            decorator = match.group(1).strip()
            marker_content = match.group(2).strip()

            # キーワード解析
            keyword_result = self.keyword_parser.parse(decorator)
            if keyword_result.type == "error":
                return error_node(f"Invalid decorator: {decorator}")

            # マーカーコンテンツ解析
            node = Node(
                type="marker",
                content=marker_content,
                attributes={
                    "keyword_type": keyword_result.type,
                    "processed_by": "specialized_parser",
                    "decorator": decorator,
                    "line_number": 1,
                    "column": 1,
                },
            )
            return node

        except Exception as e:
            return error_node(f"Marker parsing error: {e}")

    def parse_new_format_content(self, content: str) -> Node:
        """新フォーマットコンテンツ解析（NewFormatProcessor統合）

        Args:
            content: 新フォーマットコンテンツ

        Returns:
            解析結果ノード
        """
        try:
            matches = self.new_format_pattern.findall(content)
            if not matches:
                return error_node("No new format patterns found")

            processed_content = content
            format_data = []

            for match in matches:
                format_info = self._parse_new_format_expression(match)
                format_data.append(format_info)
                # 処理済みマークで置換（実際の変換は後段）
                processed_content = processed_content.replace(
                    f"{{{{{match}}}}}", f"[NEW_FORMAT:{len(format_data)-1}]"
                )

            return Node(
                type="new_format",
                content=processed_content,
                attributes={
                    "format_data": format_data,
                    "original_formats": matches,
                    "processed_by": "specialized_parser",
                    "line_number": 1,
                    "column": 1,
                },
            )

        except Exception as e:
            return error_node(f"New format parsing error: {e}")

    def parse_ruby_content(self, content: str) -> Node:
        """ルビコンテンツ解析（RubyFormatProcessor統合）

        Args:
            content: ルビコンテンツ

        Returns:
            解析結果ノード
        """
        try:
            matches = self.ruby_pattern.findall(content)
            if not matches:
                return error_node("No ruby patterns found")

            processed_content = content
            ruby_data = []

            for base_text, ruby_text in matches:
                ruby_info = {
                    "base": base_text.strip(),
                    "ruby": ruby_text.strip(),
                    "type": "ruby_annotation",
                }
                ruby_data.append(ruby_info)

                # 処理済みマークで置換
                original = f"|{base_text}|{ruby_text}|"
                processed_content = processed_content.replace(
                    original, f"[RUBY:{len(ruby_data)-1}]"
                )

            return Node(
                type="ruby_format",
                content=processed_content,
                attributes={
                    "ruby_data": ruby_data,
                    "processed_by": "specialized_parser",
                    "line_number": 1,
                    "column": 1,
                },
            )

        except Exception as e:
            return error_node(f"Ruby parsing error: {e}")

    def parse_inline_content(self, content: str) -> Node:
        """インラインコンテンツ解析（InlineMarkerProcessor統合）

        Args:
            content: インラインコンテンツ

        Returns:
            解析結果ノード
        """
        try:
            matches = self.inline_pattern.findall(content)
            if not matches:
                return error_node("No inline patterns found")

            processed_content = content
            inline_data = []

            for match in matches:
                inline_info = self._parse_inline_expression(match)
                inline_data.append(inline_info)
                # 処理済みマークで置換
                processed_content = processed_content.replace(
                    f"`{match}`", f"[INLINE:{len(inline_data)-1}]"
                )

            return Node(
                type="inline_format",
                content=processed_content,
                attributes={
                    "inline_data": inline_data,
                    "processed_by": "specialized_parser",
                    "line_number": 1,
                    "column": 1,
                },
            )

        except Exception as e:
            return error_node(f"Inline parsing error: {e}")

    def parse_generic_special(self, content: str) -> Node:
        """汎用特殊処理

        Args:
            content: 処理対象コンテンツ

        Returns:
            解析結果ノード
        """
        # 特殊な処理が不要な場合のフォールバック
        return Node(
            type="generic_special",
            content=content,
            attributes={
                "processed_by": "specialized_parser",
                "format_type": "generic",
                "line_number": 1,
                "column": 1,
            },
        )

    def validate(self, content: str) -> bool:
        """コンテンツ検証

        Args:
            content: 検証対象コンテンツ

        Returns:
            検証結果
        """
        try:
            if not content:
                return False

            # 各種パターンのチェック
            has_marker = bool(self.marker_pattern.search(content))
            has_new_format = bool(self.new_format_pattern.search(content))
            has_ruby = bool(self.ruby_pattern.search(content))
            has_inline = bool(self.inline_pattern.search(content))

            return has_marker or has_new_format or has_ruby or has_inline

        except Exception as e:
            self.logger.warning(f"検証エラー: {e}")
            return False

    # プライベートヘルパーメソッド
    def _init_new_format_patterns(self) -> Dict[str, re.Pattern[str]]:
        """新フォーマットパターン初期化"""
        return {
            "variable": re.compile(r"\$([a-zA-Z_][a-zA-Z0-9_]*)"),
            "function": re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]*)\)"),
            "attribute": re.compile(r"@([a-zA-Z_][a-zA-Z0-9_]*)"),
        }

    def _init_ruby_format_patterns(self) -> Dict[str, re.Pattern[str]]:
        """ルビフォーマットパターン初期化"""
        return {
            "kanji": re.compile(r"[\u4e00-\u9faf]+"),
            "hiragana": re.compile(r"[\u3041-\u3096]+"),
            "katakana": re.compile(r"[\u30a1-\u30f6]+"),
        }

    def _init_inline_patterns(self) -> Dict[str, re.Pattern[str]]:
        """インラインパターン初期化"""
        return {
            "code": re.compile(r"code:([^`]+)"),
            "math": re.compile(r"math:([^`]+)"),
            "link": re.compile(r"link:([^`]+)"),
        }

    def _parse_new_format_expression(self, expression: str) -> Dict[str, Any]:
        """新フォーマット式解析"""
        expr_type = "unknown"
        data = {"expression": expression}

        # パターン判定
        for pattern_name, pattern in self._new_format_patterns.items():
            if pattern.search(expression):
                expr_type = pattern_name
                match = pattern.search(expression)
                if match:
                    groups: Any = list(match.groups())
                    data["match_groups"] = groups
                break

        data["type"] = expr_type
        return data

    def _parse_inline_expression(self, expression: str) -> Dict[str, Any]:
        """インライン式解析"""
        expr_type = "text"  # デフォルト
        data = {"expression": expression}

        # パターン判定
        for pattern_name, pattern in self._inline_patterns.items():
            if pattern.search(expression):
                expr_type = pattern_name
                match = pattern.search(expression)
                if match:
                    data["content"] = match.group(1)
                break

        data["type"] = expr_type
        return data


# レガシー互換関数
def parse_marker(content: str) -> Node:
    """マーカー解析（レガシー互換）

    Warning:
        この関数は後方互換性のために提供されています。
        新しいコードではSpecializedParserクラスを使用してください。
    """
    warnings.warn(
        "parse_marker() is deprecated. Use SpecializedParser instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    parser = SpecializedParser()
    return parser.parse_marker_content(content)


def parse_new_format(content: str) -> Node:
    """新フォーマット解析（レガシー互換）"""
    warnings.warn(
        "parse_new_format() is deprecated. Use SpecializedParser instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    parser = SpecializedParser()
    return parser.parse_new_format_content(content)


def parse_ruby_format(content: str) -> Node:
    """ルビフォーマット解析（レガシー互換）"""
    warnings.warn(
        "parse_ruby_format() is deprecated. Use SpecializedParser instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    parser = SpecializedParser()
    return parser.parse_ruby_content(content)


# エクスポート定義
__all__ = [
    # 統合エラークラス
    "SpecializedParsingError",
    "MarkerValidationError",
    "FormatProcessingError",
    # メインクラス
    "SpecializedParser",
    # レガシー互換関数
    "parse_marker",
    "parse_new_format",
    "parse_ruby_format",
]
