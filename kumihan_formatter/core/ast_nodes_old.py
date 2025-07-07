"""AST Node definitions for Kumihan-Formatter

This module contains the Abstract Syntax Tree node definitions
used throughout the parsing and rendering pipeline.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


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
    attributes: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.attributes is None:
            self.attributes = {}

    def add_attribute(self, key: str, value: Any) -> None:
        """Add an attribute to the node"""
        if self.attributes is None:
            self.attributes = {}
        self.attributes[key] = value

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

    def get_heading_level(self) -> Optional[int]:
        """Get heading level (1-5) or None if not a heading"""
        if self.type.startswith("h") and len(self.type) == 2:
            try:
                return int(self.type[1])
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

    def find_children_by_type(self, node_type: str) -> List["Node"]:
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
        self._attributes: dict[str, Any] = {}

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


# Convenience functions for common node types
def paragraph(content: Union[str, List[Any]]) -> Node:
    """Create a paragraph node"""
    return NodeBuilder("p").content(content).build()


def heading(
    level: int, content: Union[str, List[Any]], heading_id: Optional[str] = None
) -> Node:
    """Create a heading node"""
    builder = NodeBuilder(f"h{level}").content(content)
    if heading_id:
        builder.id(heading_id)
    return builder.build()


def strong(content: Union[str, List[Any]]) -> Node:
    """Create a strong (bold) node"""
    return NodeBuilder("strong").content(content).build()


def emphasis(content: Union[str, List[Any]]) -> Node:
    """Create an emphasis (italic) node"""
    return NodeBuilder("em").content(content).build()


def div_box(content: Union[str, List[Any]]) -> Node:
    """Create a div with box class"""
    return NodeBuilder("div").css_class("box").content(content).build()


def highlight(content: Union[str, List[Any]], color: Optional[str] = None) -> Node:
    """Create a highlight div"""
    builder = NodeBuilder("div").css_class("highlight").content(content)
    if color:
        builder.style(f"background-color:{color}")
    return builder.build()


def unordered_list(items: List[Node]) -> Node:
    """Create an unordered list"""
    return NodeBuilder("ul").content(items).build()


def ordered_list(items: List[Node]) -> Node:
    """Create an ordered list"""
    return NodeBuilder("ol").content(items).build()


def list_item(content: Union[str, List[Any], Node]) -> Node:
    """Create a list item"""
    return NodeBuilder("li").content(content).build()


def details(summary: str, content: Union[str, List[Any]]) -> Node:
    """Create a details/summary block"""
    return NodeBuilder("details").attribute("summary", summary).content(content).build()


def error_node(message: str, line_number: Optional[int] = None) -> Node:
    """Create an error node"""
    builder = NodeBuilder("error").content(message)
    if line_number is not None:
        builder.attribute("line", line_number)
    return builder.build()


def image_node(filename: str, alt_text: Optional[str] = None) -> Node:
    """Create an image node"""
    builder = NodeBuilder("image").content(filename)
    if alt_text:
        builder.attribute("alt", alt_text)
    return builder.build()


def toc_marker() -> Node:
    """Create a table of contents marker node"""
    return NodeBuilder("toc").content("").build()


# AST utility functions
def flatten_text_nodes(content: List[Any]) -> List[Any]:
    """Flatten consecutive text nodes in a content list"""
    if not content:
        return content

    result = []
    current_text = ""

    for item in content:
        if isinstance(item, str):
            current_text += item
        else:
            if current_text:
                result.append(current_text)
                current_text = ""
            result.append(item)

    if current_text:
        result.append(current_text)

    return result


def count_nodes_by_type(nodes: List[Node]) -> Dict[str, int]:
    """Count nodes by type in a list"""
    counts: dict[str, int] = {}
    for node in nodes:
        if isinstance(node, Node):
            counts[node.type] = counts.get(node.type, 0) + 1
    return counts


def find_all_headings(nodes: List[Node]) -> List[Node]:
    """Find all heading nodes recursively"""
    headings = []
    for node in nodes:
        if isinstance(node, Node):
            if node.is_heading():
                headings.append(node)
            # Recursively search in content
            if isinstance(node.content, list):
                headings.extend(find_all_headings(node.content))
    return headings


def validate_ast(nodes: List[Node]) -> List[str]:
    """Validate AST structure and return list of issues"""
    issues = []

    for i, node in enumerate(nodes):
        if not isinstance(node, Node):
            issues.append(f"Item {i} is not a Node instance: {type(node)}")
            continue

        if not node.type:
            issues.append(f"Node {i} has empty type")
            continue

        if node.content is None:
            issues.append(f"Node {i} ({node.type}) has None content")
            continue

        # Validate heading hierarchy
        if node.is_heading():
            level = node.get_heading_level()
            if level and not (1 <= level <= 5):
                issues.append(f"Node {i} has invalid heading level: {level}")

    return issues
