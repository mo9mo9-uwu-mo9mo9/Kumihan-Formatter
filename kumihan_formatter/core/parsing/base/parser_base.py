"""統一パーサー基底クラス

Issue #880 Phase 2: すべてのパーサーの共通基盤
既存のBaseBlockParserとBaseParserを統合
"""

import re
from typing import Any, Dict, List, Tuple, Union, cast

from ...ast_nodes import Node, error_node
from ...utilities.logger import get_logger
from ..protocols import ParseResult


class UnifiedParserBase:
    """統一パーサー基底クラス

    既存のBaseBlockParserとBaseParserの機能を統合
    すべてのパーサーの共通基盤を提供
    """

    def __init__(self, parser_type: str = "unknown"):
        """基底パーサーの初期化

        Args:
            parser_type: パーサーの種類（ParserType定数を使用）
        """
        self.logger = get_logger(self.__class__.__name__)
        self.parser_type = parser_type

        # 共通パターン定義（既存コードから統合）
        self._setup_common_patterns()

        # パフォーマンス向上のためのキャッシュ
        self._cache: Dict[str, Any] = {}
        self._cache_enabled = True

        # エラー・警告管理
        self._errors: List[str] = []
        self._warnings: List[str] = []

        # パフォーマンス統計（Issue #1082: CI対応）
        self._performance_stats: Dict[str, Any] = {
            "parse_count": 0,
            "total_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

    def _setup_common_patterns(self) -> None:
        """共通正規表現パターンの設定"""
        # Kumihan記法パターン（BaseParserから）
        self._NEW_FORMAT_PATTERN = re.compile(
            r"^#\s*([^#]+?)\s*#([^#]*?)##$", re.MULTILINE
        )
        self._INLINE_CONTENT_PATTERN = re.compile(r"^#\s*([^#]+?)\s*#([^#]*?)##$")
        self._FORMAT_CHECK_PATTERN = re.compile(r"^#[^#]*#[^#]*##$")
        self._COLOR_ATTRIBUTE_PATTERN = re.compile(r"\[color:([#a-zA-Z0-9]+)\]")
        self._KEYWORD_SPLIT_PATTERN = re.compile(r"[+\-,]")

        # ブロック解析パターン（BaseBlockParserから）
        self._BLOCK_START_PATTERN = re.compile(r"^#+\s*")
        self._BLOCK_END_PATTERN = re.compile(r"##\s*$")
        self._LIST_PATTERN = re.compile(r"^\s*[-*+]\s+")
        self._NUMBERED_LIST_PATTERN = re.compile(r"^\s*\d+\.\s+")

        # 共通マーカー定義
        self.HASH_MARKERS = ["#", "##", "###", "####", "#####"]
        self.BLOCK_END_MARKERS = ["##", "###", "####", "#####"]

    def get_parser_type(self) -> str:
        """パーサーの種類を返す"""
        return self.parser_type

    def can_parse(self, content: Union[str, List[str]]) -> bool:
        """解析可能性の基本チェック

        サブクラスでオーバーライドして具体的な判定を実装
        """
        if not content:
            return False

        # 基本的な型チェック
        if isinstance(content, str):
            return len(content.strip()) > 0
        elif isinstance(content, list):
            return len(content) > 0 and any(
                isinstance(line, str) and line.strip() for line in content
            )

        return False

    def parse(self, content: Union[str, List[str]], **kwargs: Any) -> Node:
        """基本解析メソッド

        サブクラスでオーバーライドして具体的な解析を実装
        """
        self._clear_errors_warnings()

        try:
            # キャッシュチェック
            if self._cache_enabled and isinstance(content, str):
                cache_key = f"{self.parser_type}:{hash(content)}"
                if cache_key in self._cache:
                    self.logger.debug(f"Cache hit for {self.parser_type} parser")
                    return cast(Node, self._cache[cache_key])

            # 前処理
            processed_content = self._preprocess_content(content)

            # サブクラスの具体的な解析メソッドを呼び出し
            result = self._parse_implementation(processed_content, **kwargs)

            # キャッシュに保存
            if self._cache_enabled and isinstance(content, str):
                self._cache[cache_key] = result

            return result

        except Exception as e:
            self.logger.error(f"Parse error in {self.parser_type}: {e}")
            self._errors.append(f"解析エラー: {str(e)}")
            return error_node(f"Parse error: {e}")

    def _parse_implementation(
        self, content: Union[str, List[str]], **kwargs: Any
    ) -> Node:
        """具体的な解析実装（サブクラスでオーバーライド必須）"""
        raise NotImplementedError("Subclasses must implement _parse_implementation")

    def _preprocess_content(
        self, content: Union[str, List[str]]
    ) -> Union[str, List[str]]:
        """コンテンツの前処理"""
        if isinstance(content, str):
            # 改行の正規化
            content = content.replace("\r\n", "\n").replace("\r", "\n")
            # 末尾の空白削除
            content = content.rstrip()
        elif isinstance(content, list):
            # 各行の前処理
            content = [
                line.rstrip() if isinstance(line, str) else str(line)
                for line in content
            ]

        return content

    def _clear_errors_warnings(self) -> None:
        """エラー・警告のクリア"""
        self._errors.clear()
        self._warnings.clear()

    def get_errors(self) -> List[str]:
        """エラーメッセージを取得"""
        return self._errors.copy()

    def get_warnings(self) -> List[str]:
        """警告メッセージを取得"""
        return self._warnings.copy()

    def add_error(self, message: str) -> None:
        """エラーメッセージを追加"""
        self._errors.append(message)
        self.logger.error(f"{self.parser_type} parser: {message}")

    def add_warning(self, message: str) -> None:
        """警告メッセージを追加"""
        self._warnings.append(message)
        self.logger.warning(f"{self.parser_type} parser: {message}")

    def _contains_malicious_content(self, content: Any) -> bool:
        """悪意のあるコンテンツの検出"""
        if not isinstance(content, str):
            return False

        # 基本的なセキュリティチェック
        malicious_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"data:.*base64",
            r"vbscript:",
        ]

        content_lower = content.lower()
        for pattern in malicious_patterns:
            if re.search(pattern, content_lower):
                self.add_warning(f"潜在的に危険なコンテンツを検出: {pattern}")
                return True

        return False

    def clear_cache(self) -> None:
        """キャッシュをクリア"""
        self._cache.clear()
        self.logger.debug(f"Cache cleared for {self.parser_type} parser")

    def set_cache_enabled(self, enabled: bool) -> None:
        """キャッシュの有効/無効を設定"""
        self._cache_enabled = enabled
        if not enabled:
            self.clear_cache()

    def get_cache_stats(self) -> Dict[str, Any]:
        """キャッシュ統計情報を取得"""
        return {
            "enabled": self._cache_enabled,
            "size": len(self._cache),
            "parser_type": self.parser_type,
        }

    def create_parse_result(self, node: Node, **kwargs: Any) -> ParseResult:
        """解析結果オブジェクトを作成"""
        return ParseResult(
            node=node,
            parser_type=self.parser_type,
            metadata=kwargs.get("metadata", {}),
            errors=self.get_errors(),
            warnings=self.get_warnings(),
        )


class CommonParserMixin:
    """共通パーサー機能ミックスイン

    Issue #912: パーサー統合で共通化される機能
    """

    def _validate_input(self, text: str) -> bool:
        """入力検証"""
        return isinstance(text, str) and bool(text.strip())

    def _handle_error(self, error: Exception, context: str) -> Node:
        """統一エラーハンドリング"""
        error_msg = f"Error in {context}: {error}"
        if hasattr(self, "logger"):
            self.logger.error(error_msg)
        if hasattr(self, "add_error"):
            self.add_error(error_msg)
        return error_node(error_msg)

    def _normalize_content(self, content: str) -> str:
        """コンテンツの正規化"""
        if not isinstance(content, str):
            return ""

        # 改行の統一
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # 余分な空白の削除
        lines = content.split("\n")
        normalized_lines = []
        for line in lines:
            normalized_lines.append(line.rstrip())

        return "\n".join(normalized_lines)

    def _is_empty_content(self, content: str) -> bool:
        """空コンテンツの判定"""
        return not content or not content.strip()

    def _extract_attributes(self, content: str) -> Tuple[str, Dict[str, str]]:
        """属性の抽出（共通ロジック）

        Returns:
            (属性を除いたコンテンツ, 属性辞書)
        """
        import re

        attributes = {}

        # color属性の抽出
        color_pattern = re.compile(r"\[color:([#a-zA-Z0-9]+)\]")
        color_matches = color_pattern.findall(content)
        if color_matches:
            attributes["color"] = color_matches[0]
            content = color_pattern.sub("", content)

        # style属性の抽出
        style_pattern = re.compile(r"\[style:([^]]+)\]")
        style_matches = style_pattern.findall(content)
        if style_matches:
            attributes["style"] = style_matches[0]
            content = style_pattern.sub("", content)

        # class属性の抽出
        class_pattern = re.compile(r"\[class:([^]]+)\]")
        class_matches = class_pattern.findall(content)
        if class_matches:
            attributes["class"] = class_matches[0]
            content = class_pattern.sub("", content)

        return content.strip(), attributes
