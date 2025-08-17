"""カスタムキーワード解析機能

カスタム・拡張キーワード解析処理:
- カスタムキーワード処理
- インライン記法マッピング
- ユーザー定義キーワード
- 拡張機能

Issue #914: アーキテクチャ最適化 - keyword_parser.py分割
"""

import re
from typing import Any, Dict, List, Optional, Set

from ....ast_nodes import (
    Node,
    NodeBuilder,
    create_node,
    emphasis,
    highlight,
    strong,
)

# from ...base.parser_protocols import ParseContext, ParseResult


class CustomKeywordParser:
    """カスタムキーワード解析クラス

    カスタム・拡張機能を提供:
    - ユーザー定義キーワード管理
    - インライン記法マッピング
    - 拡張機能処理
    - 非推奨機能管理
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """初期化

        Args:
            config: 設定辞書
        """
        self.config = config or {}
        self._setup_custom_registry()
        self._setup_inline_mapping()
        self._setup_extension_features()

    def _setup_custom_registry(self) -> None:
        """カスタムキーワードレジストリの設定"""
        # カスタムキーワード（ユーザー定義）
        self.custom_keywords: Dict[str, Dict[str, Any]] = {}

        # 非推奨キーワード
        self.deprecated_keywords: Set[str] = set()

        # 拡張キーワード
        self.extension_keywords: Dict[str, Dict[str, Any]] = {}

    def _setup_inline_mapping(self) -> None:
        """インライン記法マッピングの設定"""
        self._inline_pattern = re.compile(r"#\s*([^#]+?)\s*#([^#]+?)##")
        self._inline_keyword_mapping = {
            "太字": strong,
            "イタリック": emphasis,
            "ハイライト": highlight,
            "下線": lambda text: NodeBuilder("u").content(text).build(),
            "コード": lambda text: NodeBuilder("code").content(text).build(),
            "取り消し線": lambda text: NodeBuilder("del").content(text).build(),
            "ルビ": self._create_ruby_node,
        }

    def _setup_extension_features(self) -> None:
        """拡張機能の設定"""
        self.extension_features = {
            "auto_link": True,
            "emoji_support": True,
            "math_notation": False,
            "code_highlighting": True,
        }

    def register_keyword(self, keyword: str, definition: Dict[str, Any]) -> None:
        """カスタムキーワードを登録

        Args:
            keyword: キーワード名
            definition: キーワード定義
        """
        self.custom_keywords[keyword] = definition

    def unregister_keyword(self, keyword: str) -> bool:
        """カスタムキーワードの登録解除

        Args:
            keyword: 登録解除対象のキーワード

        Returns:
            解除成功時True
        """
        if keyword in self.custom_keywords:
            del self.custom_keywords[keyword]
            return True
        return False

    def deprecate_keyword(self, keyword: str) -> None:
        """キーワードを非推奨にマーク

        Args:
            keyword: 非推奨対象のキーワード
        """
        self.deprecated_keywords.add(keyword)

    def get_keyword_suggestions(self, partial: str) -> List[str]:
        """部分文字列にマッチするキーワード候補を取得

        Args:
            partial: 部分文字列

        Returns:
            マッチするキーワードのリスト
        """
        all_keywords = set(self.custom_keywords.keys()) | set(
            self.extension_keywords.keys()
        )
        suggestions = [kw for kw in all_keywords if partial.lower() in kw.lower()]
        return sorted(suggestions)

    def validate_keyword(self, keyword: str) -> Dict[str, Any]:
        """キーワードの妥当性を検証

        Args:
            keyword: 検証対象のキーワード

        Returns:
            検証結果辞書
        """
        result = {
            "valid": False,
            "type": None,
            "definition": None,
            "deprecated": False,
            "suggestions": [],
        }

        definition = self.get_keyword_definition(keyword)
        if definition:
            result["valid"] = True
            result["type"] = definition.get("type")
            result["definition"] = definition
            result["deprecated"] = keyword in self.deprecated_keywords
        else:
            # 類似キーワードの提案
            result["suggestions"] = self.get_keyword_suggestions(keyword)

        return result

    def get_keyword_definition(self, keyword: str) -> Optional[Dict[str, Any]]:
        """キーワード定義を取得

        Args:
            keyword: キーワード名

        Returns:
            キーワード定義、見つからない場合はNone
        """
        if keyword in self.custom_keywords:
            return self.custom_keywords[keyword]
        elif keyword in self.extension_keywords:
            return self.extension_keywords[keyword]
        else:
            return None

    def process_inline_keywords(self, text: str) -> List[Node]:
        """インライン記法の処理

        Args:
            text: 処理対象のテキスト

        Returns:
            処理済みノードのリスト
        """
        nodes = []
        last_end = 0

        for match in self._inline_pattern.finditer(text):
            # マッチ前のテキスト
            if match.start() > last_end:
                plain_text = text[last_end : match.start()]
                if plain_text:
                    nodes.append(create_node("text", content=plain_text))

            # インライン記法の処理
            keyword = match.group(1).strip()
            content = match.group(2).strip()

            if keyword in self._inline_keyword_mapping:
                handler = self._inline_keyword_mapping[keyword]
                node = handler(content)
                nodes.append(node)
            else:
                # 未知のキーワード
                nodes.append(create_node("unknown_inline", content=match.group(0)))

            last_end = match.end()

        # 最後の部分
        if last_end < len(text):
            remaining_text = text[last_end:]
            if remaining_text:
                nodes.append(create_node("text", content=remaining_text))

        return nodes

    def _create_ruby_node(self, text: str) -> Node:
        """ルビノードの作成（インライン記法用）

        Args:
            text: ルビテキスト

        Returns:
            ルビノード
        """
        if "|" in text:
            parts = text.split("|", 1)
            if len(parts) == 2:
                return (
                    NodeBuilder("ruby")
                    .content(parts[0].strip())
                    .attribute("data-ruby", parts[1].strip())
                    .build()
                )

        return NodeBuilder("span").content(text).build()

    def register_extension_keyword(
        self, keyword: str, definition: Dict[str, Any]
    ) -> None:
        """拡張キーワードを登録

        Args:
            keyword: キーワード名
            definition: キーワード定義
        """
        self.extension_keywords[keyword] = definition

    def enable_extension_feature(self, feature: str) -> bool:
        """拡張機能を有効化

        Args:
            feature: 機能名

        Returns:
            有効化成功時True
        """
        if feature in self.extension_features:
            self.extension_features[feature] = True
            return True
        return False

    def disable_extension_feature(self, feature: str) -> bool:
        """拡張機能を無効化

        Args:
            feature: 機能名

        Returns:
            無効化成功時True
        """
        if feature in self.extension_features:
            self.extension_features[feature] = False
            return True
        return False

    def get_extension_status(self) -> Dict[str, bool]:
        """拡張機能の状態を取得

        Returns:
            拡張機能状態辞書
        """
        return self.extension_features.copy()

    def get_custom_keyword_statistics(self) -> Dict[str, Any]:
        """カスタムキーワード統計情報を取得

        Returns:
            統計情報辞書
        """
        return {
            "custom_keywords": len(self.custom_keywords),
            "extension_keywords": len(self.extension_keywords),
            "deprecated_keywords": len(self.deprecated_keywords),
            "total_custom": len(self.custom_keywords) + len(self.extension_keywords),
            "enabled_extensions": sum(
                1 for enabled in self.extension_features.values() if enabled
            ),
        }
