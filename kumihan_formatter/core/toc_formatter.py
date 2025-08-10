"""TOC Formatter class for Kumihan-Formatter

This module contains the TOC formatting logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .toc_generator import TOCEntry


class TOCFormatter:
    """
    目次のHTMLフォーマット（スタイル・リンク・インデント）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#目次出力形式
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - スタイル詳細: /docs/toc_styling.md

    関連クラス:
    - TOCGenerator: フォーマット対象の目次データ
    - TOCEntry: フォーマット対象のエントリー
    - HTMLFormatter: HTML整形と連携

    責務:
    - 目次のHTMLリスト生成
    - アンカーリンクの作成
    - インデントと階層表現
    - CSSクラスの付与
    """

    def __init__(self, css_classes: dict[str, str] | None = None) -> None:
        """Initialize TOCFormatter with optional custom CSS classes"""
        self.css_classes = css_classes or {
            "container": "toc",
            "list": "toc-list",
            "item": "toc-level-{level}",
        }

    def format_simple_list(self, entries: list[TOCEntry]) -> str:
        """Format TOC as a simple flat list"""
        lines: list[str] = []

        def add_entry(entry: TOCEntry) -> None:
            indent = "  " * (entry.level - 1)
            title = entry.get_text_content()
            lines.append(f"{indent}- {title}")

            for child in entry.children:
                add_entry(child)

        for entry in entries:
            add_entry(entry)

        return "\n".join(lines)

    def format_numbered_list(self, entries: list[TOCEntry]) -> str:
        """Format TOC as a numbered list"""
        lines: list[str] = []
        counters: dict[int, int] = {}  # Track counters for each level

        def add_entry(entry: TOCEntry) -> None:
            level = entry.level

            # Initialize or increment counter for this level
            if level not in counters:
                counters[level] = 1
            else:
                counters[level] += 1

            # Reset counters for deeper levels
            levels_to_reset = [level_key for level_key in counters.keys() if level_key > level]
            for level_key in levels_to_reset:
                del counters[level_key]

            # Build number prefix
            number_parts = []
            for i in range(1, level + 1):
                if i in counters:
                    number_parts.append(str(counters[i]))

            number = ".".join(number_parts)
            indent = "  " * (level - 1)
            title = entry.get_text_content()
            lines.append(f"{indent}{number}. {title}")

            for child in entry.children:
                add_entry(child)

        for entry in entries:
            add_entry(entry)

        return "\n".join(lines)

    def format_json(self, entries: list[TOCEntry]) -> str:
        """Format TOC as JSON structure"""
        import json

        def entry_to_dict(entry: TOCEntry) -> dict[str, Any]:
            return {
                "level": entry.level,
                "title": entry.get_text_content(),
                "id": entry.heading_id,
                "children": [entry_to_dict(child) for child in entry.children],
            }

        toc_data = [entry_to_dict(entry) for entry in entries]
        return json.dumps(toc_data, ensure_ascii=False, indent=2)

    def format_html(self, entries: list[TOCEntry]) -> str:
        """Format TOC as HTML with proper structure and CSS classes"""
        if not entries:
            return ""

        container_class = self.css_classes.get("container", "toc")
        list_class = self.css_classes.get("list", "toc-list")
        html_parts = [f'<div class="{container_class}">', f'<ul class="{list_class}">']

        def add_entry(entry: TOCEntry) -> None:
            import html

            # HTML-escape the title
            escaped_title = html.escape(entry.get_text_content())
            item_template = self.css_classes.get("item", "toc-level-{level}")
            level_class = (
                item_template.format(level=entry.level)
                if "{level}" in item_template
                else item_template
            )

            html_parts.append(f'<li class="{level_class}">')
            html_parts.append(f'<a href="#{entry.heading_id}">{escaped_title}</a>')

            # Add nested entries
            if entry.children:
                html_parts.append("<ul>")
                for child in entry.children:
                    add_entry(child)
                html_parts.append("</ul>")

            html_parts.append("</li>")

        for entry in entries:
            add_entry(entry)

        html_parts.extend(["</ul>", "</div>"])
        return "\n".join(html_parts)

    def format_plain_text(self, entries: list[TOCEntry]) -> str:
        """Format TOC as plain text with numbered hierarchy"""
        if not entries:
            return ""

        lines: list[str] = []
        counters: dict[int, int] = {}  # Track counters for each level

        def add_entry(entry: TOCEntry) -> None:
            level = entry.level

            # Initialize or increment counter for this level
            if level not in counters:
                counters[level] = 1
            else:
                counters[level] += 1

            # Reset counters for deeper levels
            levels_to_reset = [level_key for level_key in counters.keys() if level_key > level]
            for level_key in levels_to_reset:
                del counters[level_key]

            # Build number prefix
            number_parts = []
            for i in range(1, level + 1):
                if i in counters:
                    number_parts.append(str(counters[i]))

            number = ".".join(number_parts)
            indent = "  " * (level - 1)
            title = entry.get_text_content()
            lines.append(f"{indent}{number}. {title}")

            # Add children
            for child in entry.children:
                add_entry(child)

        for entry in entries:
            add_entry(entry)

        return "\n".join(lines)

    def format_markdown(self, entries: list[TOCEntry]) -> str:
        """Format TOC as Markdown with proper link structure"""
        if not entries:
            return ""

        lines: list[str] = []

        def add_entry(entry: TOCEntry) -> None:
            indent = "  " * (entry.level - 1)
            title = entry.get_text_content()
            link = f"[{title}](#{entry.heading_id})"
            lines.append(f"{indent}- {link}")

            # Add children
            for child in entry.children:
                add_entry(child)

        for entry in entries:
            add_entry(entry)

        return "\n".join(lines)
