"""NodeBuilder class for fluent Node construction

This module provides a builder pattern for creating Node instances
with a fluent interface.
"""

from typing import Any, Dict

from .node import Node


class NodeBuilder:
    """
    Nodeインスタンス構築用ビルダークラス（流暢なインターフェース提供）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#複合キーワードのルール
    - アーキテクチャ: /CONTRIBUTING.md#データフロー
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - Node: 構築対象のクラス
    - KeywordParser: このクラスを使用してNode構築
    - error_node: エラー時の代替ファクトリー

    責務:
    - 流暢なインターフェースでのNode構築
    - 属性やCSSクラスの段階的設定
    - メソッドチェーンによる直感的なAPI提供
    """

    def __init__(self, node_type: str):
        self._type = node_type
        self._content = None
        self._attributes: Dict[str, Any] = {}

    def content(self, content: Any) -> "NodeBuilder":
        """Set node content"""
        self._content = content
        return self

    def attribute(self, key: str, value: Any) -> "NodeBuilder":
        """Add an attribute"""
        self._attributes[key] = value
        return self

    def css_class(self, class_name: str) -> "NodeBuilder":
        """Add CSS class attribute"""
        return self.attribute("class", class_name)

    def id(self, id_value: str) -> "NodeBuilder":
        """Add ID attribute"""
        return self.attribute("id", id_value)

    def style(self, style_value: str) -> "NodeBuilder":
        """Add style attribute"""
        return self.attribute("style", style_value)

    def build(self) -> Node:
        """Build the node"""
        return Node(
            type=self._type, content=self._content, attributes=self._attributes.copy()
        )
