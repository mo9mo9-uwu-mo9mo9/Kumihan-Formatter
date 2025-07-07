"""Compound element renderer for Kumihan-Formatter

This module handles rendering of compound elements with multiple keywords
and complex nesting logic.
"""

from html import escape
from typing import Any, Dict, List, Tuple

from .html_utils import process_text_content, sort_keywords_by_nesting_order


class CompoundElementRenderer:
    """Renderer for compound elements with multiple keywords"""

    def __init__(self) -> None:
        """Initialize compound element renderer"""
        pass

    def render_compound_element(
        self, keywords: list[str], content: str, attributes: dict[str, Any]
    ) -> str:
        """
        Render element with multiple keywords applied

        Args:
            keywords: List of keywords to apply
            content: Content to render
            attributes: Additional attributes

        Returns:
            str: Rendered HTML with nested elements
        """
        # Sort keywords by nesting order
        sorted_keywords = sort_keywords_by_nesting_order(keywords)

        # Build nested HTML from inner to outer
        current_html = process_text_content(content)

        for keyword in reversed(sorted_keywords):
            current_html = self._wrap_with_keyword(current_html, keyword, attributes)

        return current_html

    def _wrap_with_keyword(
        self, content: str, keyword: str, attributes: dict[str, Any]
    ) -> str:
        """
        Wrap content with HTML for a specific keyword

        Args:
            content: Content to wrap
            keyword: Keyword to apply
            attributes: Additional attributes

        Returns:
            str: Wrapped HTML content
        """
        if keyword == "太字":
            return f"<strong>{content}</strong>"
        elif keyword == "イタリック":
            return f"<em>{content}</em>"
        elif keyword == "枠線":
            return f'<div class="box">{content}</div>'
        elif keyword == "ハイライト":
            return self._render_highlight(content, attributes)
        elif keyword.startswith("見出し"):
            level = keyword[-1]
            return f"<h{level}>{content}</h{level}>"
        elif keyword == "折りたたみ":
            return f"<details><summary>詳細を表示</summary>{content}</details>"
        elif keyword == "ネタバレ":
            return f'<details class="spoiler"><summary>ネタバレを表示</summary>{content}</details>'
        else:
            # Fallback for unknown keywords
            return f'<span class="{escape(keyword)}">{content}</span>'

    def _render_highlight(self, content: str, attributes: dict[str, Any]) -> str:
        """
        Render highlight element with optional color

        Args:
            content: Content to highlight
            attributes: Attributes including potential color

        Returns:
            str: HTML highlight element
        """
        style = ""
        if "color" in attributes:
            color = attributes["color"]
            if not color.startswith("#"):
                color = "#" + color
            style = f' style="background-color:{color}"'

        return f'<div class="highlight"{style}>{content}</div>'

    def render_keyword_list_item(
        self, keywords: list[str], content: str, attributes: dict[str, Any]
    ) -> str:
        """
        Render list item with keywords applied

        Args:
            keywords: List of keywords to apply
            content: Content of the list item
            attributes: Additional attributes

        Returns:
            str: HTML list item with styled content
        """
        styled_content = self.render_compound_element(keywords, content, attributes)
        return f"<li>{styled_content}</li>"

    def validate_keyword_combination(self, keywords: list[str]) -> tuple[bool, str]:
        """
        Validate that keyword combination is valid

        Args:
            keywords: List of keywords to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check for duplicate heading levels
        heading_keywords = [k for k in keywords if k.startswith("見出し")]
        if len(heading_keywords) > 1:
            return (
                False,
                f"Multiple heading levels not allowed: {', '.join(heading_keywords)}",
            )

        # Check for duplicate details types
        details_keywords = [k for k in keywords if k in ["折りたたみ", "ネタバレ"]]
        if len(details_keywords) > 1:
            return (
                False,
                f"Multiple details types not allowed: {', '.join(details_keywords)}",
            )

        # Check for unknown keywords
        known_keywords = {
            "太字",
            "イタリック",
            "枠線",
            "ハイライト",
            "折りたたみ",
            "ネタバレ",
            "見出し1",
            "見出し2",
            "見出し3",
            "見出し4",
            "見出し5",
        }

        unknown_keywords = [k for k in keywords if k not in known_keywords]
        if unknown_keywords:
            return False, f"Unknown keywords: {', '.join(unknown_keywords)}"

        return True, ""
