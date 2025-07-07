"""Table of Contents generation for Kumihan-Formatter

This module handles the generation of table of contents from heading elements.
"""

from html import escape
from typing import Any, Dict, List, Optional

from .ast_nodes import Node


class TOCEntry:
    """Represents a single entry in the table of contents"""

    def __init__(self, level: int, title: str, heading_id: str, node: Node):
        self.level = level
        self.title = title
        self.heading_id = heading_id
        self.node = node
        self.children: List["TOCEntry"] = []
        self.parent: Optional["TOCEntry"] = None

    def add_child(self, child: "TOCEntry") -> None:
        """Add a child entry"""
        child.parent = self
        self.children.append(child)

    def is_root_level(self) -> bool:
        """Check if this is a root level entry"""
        return self.parent is None

    def get_depth(self) -> int:
        """Get the depth of this entry in the hierarchy"""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth

    def get_text_content(self) -> str:
        """Get plain text content of the title"""
        # Remove any HTML tags from title
        import re

        clean_title = re.sub(r"<[^>]+>", "", self.title)
        return clean_title.strip()


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

    """Generates table of contents from heading nodes"""

    def __init__(self) -> None:
        self.entries: List[TOCEntry] = []
        self.heading_counter = 0

    def generate_toc(self, nodes: List[Node]) -> Dict[str, Any]:
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

    def _collect_headings(self, nodes: List[Node]) -> List[Dict[str, Any]]:
        """Collect all heading nodes recursively"""
        headings = []
        max_depth = 50  # Prevent infinite recursion

        def collect_recursive(node_list: List[Node], depth: int = 0) -> None:
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

    def _build_toc_structure(self, headings: List[Dict[str, Any]]) -> List[TOCEntry]:
        """Build hierarchical TOC structure"""
        if not headings:
            return []

        entries = []
        stack = []  # Stack to maintain hierarchy

        for heading in headings:
            entry = TOCEntry(
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

    def _generate_toc_html(self, entries: List[TOCEntry]) -> str:
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

    def should_generate_toc(self, nodes: List[Node]) -> bool:
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

    def get_toc_statistics(self, entries: List[TOCEntry]) -> Dict[str, Any]:
        """Get statistics about the TOC structure"""
        stats = {
            "total_entries": 0,
            "levels_used": set(),
            "max_depth": 0,
            "entries_by_level": {},
        }

        def analyze_entry(entry: TOCEntry, depth: int = 0) -> None:
            stats["total_entries"] += 1
            stats["levels_used"].add(entry.level)
            stats["max_depth"] = max(stats["max_depth"], depth)

            if entry.level not in stats["entries_by_level"]:
                stats["entries_by_level"][entry.level] = 0
            stats["entries_by_level"][entry.level] += 1

            for child in entry.children:
                analyze_entry(child, depth + 1)

        for entry in entries:
            analyze_entry(entry)

        stats["levels_used"] = sorted(list(stats["levels_used"]))

        return stats


class TOCValidator:
    """
    目次構造の検証（見出しレベル・数・範囲）

    設計ドキュメント:
    - 記法仕様: /SPEC.md#目次検証ルール
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要

    関連クラス:
    - TOCGenerator: 検証対象の目次生成クラス
    - TOCEntry: 検証対象のエントリー

    責務:
    - 見出しレベルの連続性チェック
    - 目次エントリー数の制限検証
    - 無効な目次構造の検出
    """

    """Validator for table of contents structure"""

    def __init__(self):
        self.issues = []

    def validate_toc_structure(self, entries: List[TOCEntry]) -> List[str]:
        """
        Validate TOC structure and return issues

        Args:
            entries: TOC entries to validate

        Returns:
            List[str]: List of validation issues
        """
        self.issues = []

        # Check for proper heading hierarchy
        self._validate_heading_hierarchy(entries)

        # Check for duplicate IDs
        self._validate_unique_ids(entries)

        # Check for empty titles
        self._validate_titles(entries)

        return self.issues

    def _validate_heading_hierarchy(self, entries: List[TOCEntry]) -> None:
        """Validate that heading levels follow proper hierarchy"""

        def check_hierarchy(entry_list: List[TOCEntry], parent_level: int = 0) -> None:
            for entry in entry_list:
                # Check if level jump is too large
                if entry.level > parent_level + 1 and parent_level > 0:
                    self.issues.append(
                        f"見出しレベルの飛び越し: h{parent_level} から h{entry.level} "
                        f"('{entry.get_text_content()}')"
                    )

                # Recursively check children
                check_hierarchy(entry.children, entry.level)

        check_hierarchy(entries)

    def _validate_unique_ids(self, entries: List[TOCEntry]) -> None:
        """Validate that all heading IDs are unique"""
        seen_ids = set()

        def check_ids(entry_list: List[TOCEntry]) -> None:
            for entry in entry_list:
                if entry.heading_id in seen_ids:
                    self.issues.append(
                        f"重複する見出しID: '{entry.heading_id}' "
                        f"('{entry.get_text_content()}')"
                    )
                else:
                    seen_ids.add(entry.heading_id)

                check_ids(entry.children)

        check_ids(entries)

    def _validate_titles(self, entries: List[TOCEntry]) -> None:
        """Validate that all entries have non-empty titles"""

        def check_titles(entry_list: List[TOCEntry]) -> None:
            for entry in entry_list:
                if not entry.get_text_content().strip():
                    self.issues.append(f"空の見出しタイトル (ID: {entry.heading_id})")

                check_titles(entry.children)

        check_titles(entries)


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

    """Formatter for different TOC output styles"""

    def __init__(self):
        pass

    def format_simple_list(self, entries: List[TOCEntry]) -> str:
        """Format TOC as a simple flat list"""
        lines = []

        def add_entry(entry: TOCEntry) -> None:
            indent = "  " * (entry.level - 1)
            title = entry.get_text_content()
            lines.append(f"{indent}- {title}")

            for child in entry.children:
                add_entry(child)

        for entry in entries:
            add_entry(entry)

        return "\n".join(lines)

    def format_numbered_list(self, entries: List[TOCEntry]) -> str:
        """Format TOC as a numbered list"""
        lines = []
        counters = {}  # Track counters for each level

        def add_entry(entry: TOCEntry) -> None:
            level = entry.level

            # Initialize or increment counter for this level
            if level not in counters:
                counters[level] = 1
            else:
                counters[level] += 1

            # Reset counters for deeper levels
            levels_to_reset = [l for l in counters.keys() if l > level]
            for l in levels_to_reset:
                del counters[l]

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

    def format_json(self, entries: List[TOCEntry]) -> str:
        """Format TOC as JSON structure"""
        import json

        def entry_to_dict(entry: TOCEntry) -> Dict[str, Any]:
            return {
                "level": entry.level,
                "title": entry.get_text_content(),
                "id": entry.heading_id,
                "children": [entry_to_dict(child) for child in entry.children],
            }

        toc_data = [entry_to_dict(entry) for entry in entries]
        return json.dumps(toc_data, ensure_ascii=False, indent=2)
