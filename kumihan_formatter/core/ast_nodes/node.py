"""AST Node base class for Kumihan-Formatter

This module contains the core Node class that represents
elements in the Abstract Syntax Tree.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Node:
    """
    AST基本ノードクラス（すべての要素の基盤）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#構文例
    - アーキテクチャ: /CONTRIBUTING.md#データフロー
    - 依存関係: /docs/CLASS_DEPENDENCY_MAP.md

    関連クラス:
    - NodeBuilder: このクラスのインスタンス構築
    - Parser系: このクラスを生成
    - Renderer系: このクラスを消費
    - paragraph, heading等: ファクトリー関数

    責務:
    - 解析済み文書構造の単一要素表現
    - パーサーとレンダラー間のデータ交換
    - 要素タイプ・内容・属性の統一的管理
    """

    type: str
    content: Any
    attributes: dict[str, Any] | None = None
    children: list["Node"] | None = None

    def __post_init__(self) -> None:
        if self.attributes is None:
            self.attributes = {}
        if self.children is None:
            self.children = []

    def add_attribute(self, key: str, value: Any) -> None:
        """Add an attribute to the node"""
        if self.attributes is None:
            self.attributes = {}
        self.attributes[key] = value

    @property
    def metadata(self) -> dict[str, Any]:
        """属性をmetadataとしてアクセスする（統一パーサーシステム互換）"""
        if self.attributes is None:
            self.attributes = {}
        return self.attributes

    @property
    def node_type(self) -> str:
        """ノードタイプをnode_typeとしてアクセスする（統一パーサーシステム互換）"""
        return self.type

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get an attribute value"""
        if self.attributes is None:
            return default
        return self.attributes.get(key, default)

    def has_attribute(self, key: str) -> bool:
        """Check if attribute exists"""
        if self.attributes is None:
            return False
        return key in self.attributes

    def remove_attribute(self, key: str) -> None:
        """Remove an attribute from the node"""
        if self.attributes is not None and key in self.attributes:
            del self.attributes[key]

    def add_child(self, child: "Node") -> None:
        """Add a child node"""
        if self.children is None:
            self.children = []
        self.children.append(child)

    def remove_child(self, child: "Node") -> None:
        """Remove a child node"""
        if self.children is not None and child in self.children:
            self.children.remove(child)

    def is_block_element(self) -> bool:
        """Check if this node represents a block-level element"""
        block_types = {
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "p",
            "div",
            "ul",
            "ol",
            "li",
            "blockquote",
            "pre",
            "details",
        }
        return self.type in block_types

    def is_inline_element(self) -> bool:
        """Check if this node represents an inline element"""
        inline_types = {"strong", "em", "code", "span", "a"}
        return self.type in inline_types

    def is_list_element(self) -> bool:
        """Check if this node is a list element"""
        return self.type in {"ul", "ol", "li"}

    def is_heading(self) -> bool:
        """Check if this node is a heading"""
        return self.type in {"h1", "h2", "h3", "h4", "h5"}

    def get_heading_level(self) -> int | None:
        """Get heading level (1-5) or None if not a heading"""
        if self.type.startswith("h") and len(self.type) == 2:
            try:
                level = int(self.type[1])
                # 有効な見出しレベル（1-5）のみ返す
                if 1 <= level <= 5:
                    return level
            except ValueError:
                pass
        return None

    def contains_text(self) -> bool:
        """Check if this node contains text content"""
        if isinstance(self.content, str):
            return bool(self.content.strip())
        elif isinstance(self.content, list):
            return any(
                isinstance(item, str)
                and item.strip()
                or isinstance(item, Node)
                and item.contains_text()
                for item in self.content
            )
        return False

    def get_text_content(self) -> str:
        """Extract all text content from this node and its children"""
        if isinstance(self.content, str):
            return self.content
        elif isinstance(self.content, list):
            texts = []
            for item in self.content:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, Node):
                    texts.append(item.get_text_content())
            return " ".join(texts)
        return ""

    def count_children(self) -> int:
        """Count direct children of this node"""
        if isinstance(self.content, list):
            return len(self.content)
        return 0

    def find_children_by_type(self, node_type: str) -> list["Node"]:
        """Find all direct children of a specific type"""
        if not isinstance(self.content, list):
            return []
        return [
            item
            for item in self.content
            if isinstance(item, Node) and item.type == node_type
        ]

    def walk(self) -> Any:
        """Generator that yields this node and all its descendants"""
        yield self
        if isinstance(self.content, list):
            for item in self.content:
                if isinstance(item, Node):
                    yield from item.walk()

    def add_error(self, error_message: str) -> None:
        """エラーメッセージをノードに追加（パーサーエラーハンドリング用）"""
        if self.attributes is None:
            self.attributes = {}

        # errorsキーが存在しない場合は初期化
        if "errors" not in self.attributes:
            self.attributes["errors"] = []

        # エラーメッセージを追加
        self.attributes["errors"].append(error_message)

    def has_errors(self) -> bool:
        """エラーがあるかチェック"""
        if self.attributes is None:
            return False
        errors = self.attributes.get("errors", [])
        return len(errors) > 0

    def get_errors(self) -> list[str]:
        """エラーメッセージのリストを取得"""
        if self.attributes is None:
            return []
        return self.attributes.get("errors", [])
