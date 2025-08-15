"""Factory functions for common node types

This module provides convenience functions for creating
commonly used Node instances.
"""

from typing import Any, Union

from .node import Node
from .node_builder import NodeBuilder


def create_node(node_type: str, content: Any = "", **kwargs: Any) -> Node:
    """汎用ノード作成関数 - 統一パーサーシステム用"""
    builder = NodeBuilder(node_type).content(content)

    # メタデータの設定
    if "metadata" in kwargs:
        metadata = kwargs.pop("metadata")
        if isinstance(metadata, dict):
            for key, value in metadata.items():
                builder.attribute(key, value)

    # 直接属性の設定
    for key, value in kwargs.items():
        builder.attribute(key, value)

    return builder.build()


def paragraph(
    content: Union[str, list[Any]], attributes: dict[str, Any] | None = None
) -> Node:
    """Create a paragraph node"""
    builder = NodeBuilder("paragraph").content(content)
    if attributes:
        for key, value in attributes.items():
            builder.attribute(key, value)
    return builder.build()


def heading(
    level: int, content: Union[str, list[Any]], attributes: dict[str, Any] | None = None
) -> Node:
    """Create a heading node"""
    builder = NodeBuilder(f"h{level}").content(content)
    if attributes:
        for key, value in attributes.items():
            builder.attribute(key, value)
    return builder.build()


def strong(content: Union[str, list[Any]]) -> Node:
    """Create a strong (bold) node"""
    return NodeBuilder("strong").content(content).build()


def emphasis(content: Union[str, list[Any]]) -> Node:
    """Create an emphasis (italic) node"""
    return NodeBuilder("em").content(content).build()


def div_box(content: Union[str, list[Any]]) -> Node:
    """Create a div with box class"""
    return NodeBuilder("div").css_class("box").content(content).build()


def highlight(content: Union[str, list[Any]], color: str | None = None) -> Node:
    """Create a highlight div"""
    builder = NodeBuilder("div").css_class("highlight").content(content)
    if color:
        builder.style(f"background-color:{color}")
    return builder.build()


def unordered_list(items: list[Node]) -> Node:
    """Create an unordered list"""
    return NodeBuilder("ul").content(items).build()


def ordered_list(items: list[Node]) -> Node:
    """Create an ordered list"""
    return NodeBuilder("ol").content(items).build()


def list_item(content: Union[str, list[Any], Node]) -> Node:
    """Create a list item"""
    return NodeBuilder("li").content(content).build()


def details(summary: str, content: Union[str, list[Any]]) -> Node:
    """Create a details/summary block"""
    return NodeBuilder("details").attribute("summary", summary).content(content).build()


def error_node(message: str, line_number: int | None = None) -> Node:
    """Create an error node"""
    builder = NodeBuilder("error").content(message)
    if line_number is not None:
        builder.attribute("line", line_number)
    return builder.build()


def image_node(filename: str, alt_text: str | None = None) -> Node:
    """Create an image node"""
    builder = NodeBuilder("image").content(filename)
    if alt_text:
        builder.attribute("alt", alt_text)
    return builder.build()


def toc_marker() -> Node:
    """Create a table of contents marker node - DEPRECATED in Issue #799

    目次記法は完全廃止されました。
    目次は見出しが2個以上存在する場合に自動生成されます。

    Returns:
        Node: 廃止予定のTOCマーカーノード
    """
    # Issue #799: 目次記法完全廃止 - この関数は使用されません
    return NodeBuilder("toc").content("<!-- TOC Auto-Generated -->").build()
