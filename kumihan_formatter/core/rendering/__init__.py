"""Rendering module for Kumihan-Formatter

This module provides HTML rendering capabilities through specialized renderers:
- ElementRenderer: Basic HTML elements (paragraphs, headings, lists)
- CompoundElementRenderer: Complex elements with multiple keywords
- HTMLFormatter: HTML formatting and pretty-printing utilities
- HTMLRenderer: Main renderer that coordinates all specialized renderers

Backward compatibility is maintained with the original html_renderer module.
"""

from .compound_renderer import CompoundElementRenderer as CompoundRenderer
from .element_renderer import ElementRenderer
from .html_formatter import HTMLFormatter
from .html_utils import (
    NESTING_ORDER,
    contains_html_tags,
    create_self_closing_tag,
    create_simple_tag,
    escape_html,
    process_text_content,
    render_attributes,
    sort_keywords_by_nesting_order,
)
from .main_renderer import CompoundElementRenderer, HTMLRenderer

__all__ = [
    "HTMLRenderer",
    "CompoundElementRenderer",
    "ElementRenderer",
    "CompoundRenderer",
    "HTMLFormatter",
    "escape_html",
    "render_attributes",
    "process_text_content",
    "contains_html_tags",
    "create_simple_tag",
    "create_self_closing_tag",
    "sort_keywords_by_nesting_order",
    "NESTING_ORDER",
]
