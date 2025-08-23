"""Keyword parsing functionality."""

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from .base_parser import BaseParser

if TYPE_CHECKING:
    from ..base.parser_protocols import ParseContext, ParseResult
else:
    try:
        from ..base.parser_protocols import (
            BaseParserProtocol,
            KeywordParserProtocol,
            ParseContext,
            ParseResult,
        )
    except ImportError:
        # フォールバックインポート
        from typing import Protocol

        ParseContext = Any
        ParseResult = Any
        BaseParserProtocol = Protocol
        KeywordParserProtocol = Protocol


class KeywordParser(BaseParser):
    """Parser for keyword extraction and validation.

    Issue #914 Phase 1: 統一プロトコル対応
    - BaseParserProtocol と KeywordParserProtocol を実装
    - 統一インターフェースで既存APIをラップ
    - 後方互換性を完全維持
    """

    def __init__(self, definitions: Any) -> None:
        """Initialize keyword parser.

        Args:
            definitions: Keyword definitions for validation
        """
        super().__init__()
        self.definitions = definitions

    def parse_marker_keywords(
        self, marker_content: str, context: Optional[ParseContext] = None
    ) -> Tuple[List[str], Dict[str, Any], List[str]]:
        """Parse keywords from marker content.

        Args:
            marker_content: Content of marker to parse

        Returns:
            Tuple of (keywords, attributes, errors)
        """
        if not isinstance(marker_content, str):
            return [], {}, ["Invalid marker content type"]

        keywords: List[str] = []
        attributes: Dict[str, Any] = {}
        errors: List[str] = []

        marker_content = marker_content.strip()
        if not marker_content:
            return keywords, attributes, errors

        # Check for ruby content
        if marker_content.startswith("ルビ "):
            ruby_content = marker_content[3:].strip()
            ruby_result = self._parse_ruby_content(ruby_content)
            if ruby_result:
                attributes["ruby"] = ruby_result
                return keywords, attributes, errors

        # Check for compound keywords (with + separator)
        if "+" in marker_content or "＋" in marker_content:
            compound_keywords = self.split_compound_keywords(marker_content)
            for part in compound_keywords:
                if part and self._is_valid_keyword(part):
                    keywords.append(part)
        else:
            # Single keyword
            keyword = marker_content.strip()
            if keyword and self._is_valid_keyword(keyword):
                keywords.append(keyword)

        return keywords, attributes, errors

    def _process_inline_keywords(self, content: str) -> str:
        """インラインキーワード処理（list_parser_core.py用）

        Args:
            content: 処理対象のコンテンツ文字列

        Returns:
            処理されたコンテンツ文字列
        """
        if not isinstance(content, str):
            return str(content) if content is not None else ""

        # 基本的なインラインキーワード処理
        # 必要に応じて複雑な処理を追加可能
        processed_content = content.strip()

        # キーワードマーカーの基本処理
        if "# " in processed_content and " ##" in processed_content:
            # Kumihanフォーマットの基本処理
            # より複雑な処理が必要な場合は後で拡張
            pass

        return processed_content

    def split_compound_keywords(self, keyword_content: Any) -> List[str]:
        """複合キーワードを個別のキーワードに分割

        Args:
            keyword_content: 分割対象のキーワード文字列

        Returns:
            List of individual keywords
        """
        if not isinstance(keyword_content, str):
            return []

        keywords: List[str] = []
        # Check for compound keywords (+ or ＋)
        if "+" in keyword_content or "＋" in keyword_content:
            parts = re.split(r"[+＋]", keyword_content)
            for part in parts:
                part = part.strip()
                if part and self._is_valid_keyword(part):
                    keywords.append(part)
        else:
            # Single keyword
            keyword = keyword_content.strip()
            if keyword and self._is_valid_keyword(keyword):
                keywords.append(keyword)

        return keywords

    def _is_valid_keyword(self, keyword: str) -> bool:
        """Check if keyword is valid.

        Args:
            keyword: Keyword to validate

        Returns:
            True if keyword is valid
        """
        if not isinstance(keyword, str) or not keyword.strip():
            return False

        return self.definitions.is_valid_keyword(keyword) if self.definitions else True

    def parse_new_format(self, content: str) -> Any:
        """新フォーマット解析（KeywordParserProtocol用）

        Args:
            content: 解析対象のコンテンツ

        Returns:
            解析結果
        """
        # 基本実装：既存のparse_marker_keywordsを活用
        keywords, attributes, errors = self.parse_marker_keywords(content)
        return {"keywords": keywords, "attributes": attributes, "errors": errors}

    def get_node_factory(self) -> Any:
        """ノードファクトリー取得（KeywordParserProtocol用）

        Returns:
            ノードファクトリーインスタンス
        """
        # 基本実装：必要に応じて具体的なファクトリーを返す
        from ...ast_nodes.node import Node

        class SimpleNodeFactory:
            def create_node(
                self, node_type: str, content: str = "", **kwargs: Any
            ) -> Node:
                return Node(type=node_type, content=content, **kwargs)

        return SimpleNodeFactory()

    def _parse_ruby_content(self, content: Any) -> Dict[str, str]:
        """Parse ruby content for Japanese text formatting.

        Args:
            content: Content to parse for ruby text

        Returns:
            Dictionary with base_text and ruby_text if found
        """
        if not isinstance(content, str):
            return {}

        # Pattern for ruby notation: base_text(ruby_text) or base_text（ruby_text）
        ruby_pattern = r"([^()（）]+)[()（]([^()（）]+)[)）]"
        match = re.search(ruby_pattern, content)

        if match:
            base_text = match.group(1).strip()
            ruby_text = match.group(2).strip()

            if base_text and ruby_text:
                return {"base_text": base_text, "ruby_text": ruby_text}

        return {}

    # Issue #914 Phase 1: 統一プロトコル実装

    def parse(
        self, content: str, context: Optional[ParseContext] = None
    ) -> ParseResult:
        """統一パースインターフェース

        Args:
            content: パース対象のコンテンツ
            context: パースコンテキスト（オプション）

        Returns:
            ParseResult: 統一パース結果
        """
        try:
            # 既存のparse_marker_keywordsを利用
            keywords, attributes, errors = self.parse_marker_keywords(content)

            # キーワードからノードを作成
            from ...ast_nodes.node import Node

            nodes = []

            if keywords:
                for keyword in keywords:
                    node = Node(
                        type="keyword", content=keyword, attributes=attributes.copy()
                    )
                    nodes.append(node)

            # 結果作成
            success = len(errors) == 0
            result = ParseResult(
                success=success,
                nodes=nodes,
                errors=errors,
                warnings=[],
                metadata={
                    "parser": "KeywordParser",
                    "keyword_count": len(keywords),
                    "attributes": attributes,
                },
            )
            return result

        except Exception as e:
            return ParseResult(
                success=False,
                nodes=[],
                errors=[f"Keyword parsing failed: {str(e)}"],
                warnings=[],
                metadata={"parser": "KeywordParser"},
            )

    def validate(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """バリデーション - エラーリスト返却

        Args:
            content: 検証対象のコンテンツ
            context: 検証コンテキスト（オプション）

        Returns:
            List[str]: エラーメッセージリスト（空リストは成功）
        """
        errors = []

        if not isinstance(content, str):
            errors.append("Content must be a string")
            return errors

        if not content.strip():
            errors.append("Empty content provided")
            return errors

        try:
            # 既存のparse_marker_keywordsで検証
            _, _, parse_errors = self.parse_marker_keywords(content)
            errors.extend(parse_errors)

            # 追加の検証ロジック
            if "+" in content or "＋" in content:
                # 複合キーワードの検証
                keywords = self.split_compound_keywords(content)
                if not keywords:
                    errors.append("Invalid compound keyword format")
                else:
                    for keyword in keywords:
                        if not self._is_valid_keyword(keyword):
                            errors.append(f"Invalid keyword: '{keyword}'")
            else:
                # 単一キーワードの検証
                if not self._is_valid_keyword(content.strip()):
                    errors.append(f"Invalid keyword: '{content.strip()}'")

        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return errors

    def get_parser_info(self) -> Dict[str, Any]:
        """パーサー情報取得

        Returns:
            Dict[str, Any]: パーサーメタデータ
        """
        return {
            "name": "KeywordParser",
            "version": "2.0",
            "supported_formats": ["kumihan", "keyword"],
            "capabilities": [
                "keyword_parsing",
                "marker_parsing",
                "compound_keywords",
                "ruby_parsing",
                "validation",
            ],
            "description": "Kumihan keyword extraction and validation parser",
            "author": "Kumihan-Formatter Project",
        }

    def supports_format(self, format_hint: str) -> bool:
        """対応フォーマット判定

        Args:
            format_hint: フォーマットヒント文字列

        Returns:
            bool: 対応可能かどうか
        """
        supported_formats = {"kumihan", "keyword", "marker", "ruby"}
        return format_hint.lower() in supported_formats

    # KeywordParserProtocol 固有メソッドの拡張

    def parse_keywords(
        self, content: str, context: Optional[ParseContext] = None
    ) -> List[str]:
        """コンテンツからキーワードを抽出

        Args:
            content: キーワード抽出対象のコンテンツ
            context: 抽出コンテキスト（オプション）

        Returns:
            List[str]: 抽出されたキーワードのリスト
        """
        if not isinstance(content, str) or not content.strip():
            return []

        # 複合キーワードの処理
        if "+" in content or "＋" in content:
            return self.split_compound_keywords(content)

        # 単一キーワードの処理
        keyword = content.strip()
        if self._is_valid_keyword(keyword):
            return [keyword]

        return []

    def validate_keyword(
        self, keyword: str, context: Optional[ParseContext] = None
    ) -> bool:
        """キーワードの妥当性を検証

        Args:
            keyword: 検証対象のキーワード
            context: 検証コンテキスト（オプション）

        Returns:
            bool: 妥当性判定結果
        """
        return self._is_valid_keyword(keyword)

    def _sanitize_color_attribute(self, color_value: Any) -> str:
        """Sanitize color attribute value.

        Args:
            color_value: Color value to sanitize

        Returns:
            Sanitized color value
        """
        if not isinstance(color_value, str):
            return ""

        sanitized = color_value.strip()

        # Basic validation for hex colors
        if sanitized.startswith("#") and len(sanitized) in [4, 7]:
            hex_part = sanitized[1:]
            if all(c in "0123456789abcdefABCDEF" for c in hex_part):
                return sanitized

        # Named colors
        named_colors = {
            "red",
            "blue",
            "green",
            "yellow",
            "orange",
            "purple",
            "black",
            "white",
            "gray",
            "pink",
            "brown",
            "cyan",
            "magenta",
            "lime",
            "navy",
            "silver",
        }

        if sanitized.lower() in named_colors:
            return sanitized.lower()

        return "#000000"  # Default fallback color

    # 既存APIの後方互換性維持メソッド群
    # これらは既存コードで使用されているため、継続して提供

    def parse_text(self, text: str) -> List[Any]:
        """既存API互換: テキストパース

        統一プロトコルのparseメソッドを内部で使用
        """
        try:
            result = self.parse(text)
            return result.nodes
        except Exception:
            return []

    def is_valid(self, content: str) -> bool:
        """既存API互換: コンテンツの妥当性チェック

        統一プロトコルのvalidateメソッドを内部で使用
        """
        try:
            errors = self.validate(content)
            return len(errors) == 0
        except Exception:
            return False
