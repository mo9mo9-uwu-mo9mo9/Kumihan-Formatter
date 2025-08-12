"""HTML tag utilities extracted from html_utils.py

This module handles HTML tag creation and nesting priority
to maintain the 300-line limit for html_utils.py.
"""

from typing import Any

from .html_escaping import render_attributes


def create_simple_tag(
    tag: str,
    content: str = "",
    attributes: dict[str, Any] | None = None,
    self_closing: bool = False,
    formatter: Any = None,
) -> str:
    """
    Create a simple HTML tag with Phase 4 enhancements

    Args:
        tag: Tag name
        content: Tag content
        attributes: Tag attributes
        self_closing: Whether tag is self-closing
        formatter: HTMLFormatter instance for enhanced processing

    Returns:
        str: HTML tag string
    """
    # Phase 4: Use enhanced attribute rendering if formatter is provided
    if formatter:
        from .html_escaping import render_attributes_with_enhancements

        attr_str = render_attributes_with_enhancements(
            tag, attributes, content, formatter
        )
    else:
        attr_str = render_attributes(attributes)

    attr_part = f" {attr_str}" if attr_str else ""

    if self_closing:
        return f"<{tag}{attr_part} />"
    else:
        return f"<{tag}{attr_part}>{content}</{tag}>"


def create_self_closing_tag(tag: str, attributes: dict[str, Any] | None = None) -> str:
    """
    Create a self-closing HTML tag

    Args:
        tag: Tag name
        attributes: Tag attributes

    Returns:
        str: Self-closing HTML tag string
    """
    return create_simple_tag(tag, "", attributes, self_closing=True)


def get_tag_priority(tag: str) -> int:
    """
    Get nesting priority for HTML tags

    Args:
        tag: Tag name

    Returns:
        int: Priority value (lower = higher priority)
    """
    # Define nesting order priority
    priority_map = {
        "details": 0,  # 折りたたみ, ネタバレ
        "div": 1,  # 枠線, ハイライト
        "h1": 2,  # 見出し
        "h2": 3,
        "h3": 4,
        "h4": 5,
        "h5": 6,
        "h6": 7,
        "strong": 8,  # 太字
        "em": 9,  # イタリック
        "code": 10,  # インラインコード
        "span": 11,  # その他のインライン要素
    }

    return priority_map.get(tag, 999)  # Unknown tags get lowest priority


def sort_keywords_by_nesting_order(keywords: list[str]) -> list[str]:
    """
    Sort keywords by nesting order priority

    Args:
        keywords: List of keyword/tag names

    Returns:
        list[str]: Sorted keywords by nesting priority
    """
    return sorted(keywords, key=get_tag_priority)
