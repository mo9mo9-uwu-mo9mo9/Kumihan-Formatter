"""TOC Generator class for Kumihan-Formatter

This module contains the main TOC generation logic.
"""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .toc_generator import TOCEntry

from .ast_nodes import Node


class TOCGenerator:
    """
    目次生成メインクラス（見出し抽出・構造化・レンダリング）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#目次生成
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 目次仕様: /docs/toc_specification.md

    関連クラス:
    - TOCEntry: 目次エントリーのデータ構造
    - TOCValidator: 目次構造の検証
    - TOCFormatter: 目次のHTMLフォーマット
    - Parser: 目次マーカーを処理する上位クラス

    責務:
    - ASTから見出し要素の抽出
    - 見出し階層構造の構築
    - 目次エントリーのID管理
    """

    def __init__(self) -> None:
        # Import here to avoid circular import
        from .toc_generator import TOCEntry

        self.TOCEntry = TOCEntry
        self.entries: list[TOCEntry] = []
        self.heading_counter = 0

    def generate_toc(self, nodes: list[Node]) -> dict[str, Any]:
        """
        Generate table of contents from nodes

        Args:
            nodes: List of AST nodes to process

        Returns:
            Dict containing TOC data and HTML
        """
        # Collect headings
        headings = self._collect_headings(nodes)

        # Build TOC structure
        toc_entries = self._build_toc_structure(headings)

        # Generate HTML
        toc_html = self._generate_toc_html(toc_entries)

        return {
            "entries": toc_entries,
            "html": toc_html,
            "has_toc": len(toc_entries) > 0,
            "heading_count": len(headings),
        }

    def _collect_headings(self, nodes: list[Node]) -> list[dict[str, Any]]:
        """Collect all heading nodes recursively"""
        headings = []
        max_depth = 50  # Prevent infinite recursion

        def collect_recursive(node_list: list[Node], depth: int = 0) -> None:
            if depth > max_depth:
                # Prevent infinite recursion
                return

            for node in node_list:
                if isinstance(node, Node):
                    if node.is_heading():
                        level = node.get_heading_level()
                        if level:
                            # Ensure heading has an ID
                            heading_id = node.get_attribute("id")
                            if not heading_id:
                                self.heading_counter += 1
                                heading_id = f"heading-{self.heading_counter}"
                                node.add_attribute("id", heading_id)

                            headings.append(
                                {
                                    "level": level,
                                    "id": heading_id,
                                    "title": node.get_text_content(),
                                    "node": node,
                                }
                            )

                    # Recursively search in content with depth tracking
                    if isinstance(node.content, list):
                        collect_recursive(node.content, depth + 1)

        collect_recursive(nodes)
        return headings

    def _build_toc_structure(self, headings: list[dict[str, Any]]) -> list[TOCEntry]:
        """Build hierarchical TOC structure"""
        if not headings:
            return []

        entries = []
        stack: list[TOCEntry] = []  # Stack to maintain hierarchy

        for heading in headings:
            entry = self.TOCEntry(
                level=heading["level"],
                title=heading["title"],
                heading_id=heading["id"],
                node=heading["node"],
            )

            # Find the appropriate parent
            while stack and stack[-1].level >= entry.level:
                stack.pop()

            if stack:
                # Add as child to the last entry in stack
                stack[-1].add_child(entry)
            else:
                # Top-level entry
                entries.append(entry)

            stack.append(entry)

        return entries

    def _generate_toc_html(self, entries: list[TOCEntry]) -> str:
        """Generate HTML for table of contents"""
        if not entries:
            return ""

        html_parts = ['<div class="toc">']
        html_parts.append("<h2>目次</h2>")
        html_parts.append('<ul class="toc-list">')

        for entry in entries:
            html_parts.append(self._render_toc_entry(entry))

        html_parts.append("</ul>")
        html_parts.append("</div>")

        return "\n".join(html_parts)

    def _render_toc_entry(self, entry: TOCEntry) -> str:
        """Render a single TOC entry and its children"""
        escaped_title = escape(entry.get_text_content())
        escaped_id = escape(entry.heading_id)

        html_parts = []
        html_parts.append(f'<li class="toc-level-{entry.level}">')
        html_parts.append(f'<a href="#{escaped_id}">{escaped_title}</a>')

        # Render children if any
        if entry.children:
            html_parts.append("<ul>")
            for child in entry.children:
                html_parts.append(self._render_toc_entry(child))
            html_parts.append("</ul>")

        html_parts.append("</li>")

        return "\n".join(html_parts)

    def should_generate_toc(self, nodes: list[Node]) -> bool:
        """
        Determine if TOC should be generated

        Args:
            nodes: List of nodes to check

        Returns:
            bool: True if TOC should be generated
        """
        # Check for explicit TOC marker
        has_toc_marker = any(
            isinstance(node, Node) and node.type == "toc" for node in nodes
        )

        if has_toc_marker:
            return True

        # Check if there are multiple headings
        headings = self._collect_headings(nodes)
        return len(headings) >= 2

    def get_toc_statistics(self, entries: list[TOCEntry]) -> dict[str, Any]:
        """Get statistics about the TOC structure"""
        stats = {
            "total_entries": 0,
            "levels_used": set(),
            "max_depth": 0,
            "entries_by_level": {},
        }

        def analyze_entry(entry: TOCEntry, depth: int = 0) -> None:
            stats["total_entries"] += 1  # type: ignore
            stats["levels_used"].add(entry.level)  # type: ignore
            stats["max_depth"] = max(stats["max_depth"], depth)  # type: ignore

            if entry.level not in stats["entries_by_level"]:  # type: ignore
                stats["entries_by_level"][entry.level] = 0  # type: ignore
            stats["entries_by_level"][entry.level] += 1  # type: ignore

            for child in entry.children:
                analyze_entry(child, depth + 1)

        for entry in entries:
            analyze_entry(entry)

        stats["levels_used"] = sorted(list(stats["levels_used"]))  # type: ignore

        return stats
