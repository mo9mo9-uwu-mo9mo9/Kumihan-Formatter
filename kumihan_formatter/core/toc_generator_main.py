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

    堅牢性機能（Issue #799対応）:
    - エラーハンドリング強化
    - 循環参照検出・防止
    - メモリ使用量制限
    - 包括的エラーロギング
    """

    def __init__(self) -> None:
        # Import here to avoid circular import
        from kumihan_formatter.core.utilities.logger import get_logger

        from .toc_generator import TOCEntry

        self.TOCEntry = TOCEntry
        self.entries: list[TOCEntry] = []
        self.heading_counter = 0
        self.logger = get_logger(__name__)

        # 堅牢性制限値
        self.MAX_RECURSION_DEPTH = 50  # 最大再帰深度
        self.MAX_HEADINGS = 1000  # 最大見出し数（メモリ制限対応）
        self.MAX_TITLE_LENGTH = 500  # 最大タイトル長

    def generate_toc(self, nodes: list[Node]) -> dict[str, Any]:
        """
        Generate table of contents from nodes with comprehensive error handling

        Args:
            nodes: List of AST nodes to process

        Returns:
            Dict containing TOC data and HTML

        Raises:
            TOCGenerationError: 目次生成時の致命的エラー
            MemoryError: メモリ不足時
        """
        try:
            self.logger.info("TOC generation started")

            # 入力検証
            if not nodes:
                self.logger.warning("No nodes provided for TOC generation")
                return self._empty_toc_result()

            if len(nodes) > self.MAX_HEADINGS * 10:  # 大まかな制限チェック
                self.logger.warning(f"Large node count detected: {len(nodes)}")

            # Collect headings with error handling
            headings = self._collect_headings(nodes)

            if not headings:
                self.logger.info("No headings found, returning empty TOC")
                return self._empty_toc_result()

            self.logger.info(f"Found {len(headings)} headings")

            # Build TOC structure with error handling
            toc_entries = self._build_toc_structure(headings)

            # Generate HTML with error handling
            toc_html = self._generate_toc_html(toc_entries)

            result = {
                "entries": toc_entries,
                "html": toc_html,
                "has_toc": len(toc_entries) > 0,
                "heading_count": len(headings),
            }

            self.logger.info("TOC generation completed successfully")
            return result

        except MemoryError as e:
            self.logger.error(f"Memory error during TOC generation: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during TOC generation: {e}")
            # Return safe fallback instead of crashing
            return self._empty_toc_result()

    def _empty_toc_result(self) -> dict[str, Any]:
        """Return empty TOC result for error cases"""
        return {
            "entries": [],
            "html": "",
            "has_toc": False,
            "heading_count": 0,
        }

    def _collect_headings(self, nodes: list[Node]) -> list[dict[str, Any]]:
        """
        Collect all heading nodes recursively with enhanced safety measures

        Enhanced features (Issue #799):
        - 循環参照検出
        - メモリ使用量制限
        - エラーハンドリング強化
        """
        headings = []
        visited_nodes = set()  # 循環参照検出用
        max_depth = self.MAX_RECURSION_DEPTH

        try:
            self._collect_headings_recursive(
                nodes, headings, visited_nodes, max_depth, 0
            )
            self.logger.info(f"Collected {len(headings)} headings successfully")
            return headings

        except Exception as e:
            self.logger.error(f"Critical error in heading collection: {e}")
            return []

    def _collect_headings_recursive(
        self,
        node_list: list[Node],
        headings: list[dict[str, Any]],
        visited_nodes: set,
        max_depth: int,
        depth: int = 0,
    ) -> None:
        """Recursively collect headings from nodes."""
        if depth > max_depth:
            self.logger.warning(f"Maximum recursion depth ({max_depth}) exceeded")
            return

        # メモリ制限チェック - ここで早期返却
        if len(headings) >= self.MAX_HEADINGS:
            self.logger.warning(f"Maximum heading count ({self.MAX_HEADINGS}) reached")
            return

        for node in node_list:
            # 各ノード処理前にも再度チェック
            if len(headings) >= self.MAX_HEADINGS:
                self.logger.warning("Maximum heading count reached during processing")
                return

            try:
                if not isinstance(node, Node):
                    continue

                # 循環参照検出
                node_id = id(node)
                if node_id in visited_nodes:
                    self.logger.warning(
                        f"Circular reference detected for node {node_id}"
                    )
                    continue
                visited_nodes.add(node_id)

                if node.is_heading():
                    self._process_heading_node(node, headings)

                # Issue #799: Improved nested node processing
                self._process_nested_content(
                    node, headings, visited_nodes, max_depth, depth
                )

                # ノード処理完了後、visited_nodesから除去
                visited_nodes.discard(node_id)

            except Exception as e:
                self.logger.warning(f"Error processing individual node: {e}")
                continue

    def _process_heading_node(self, node: Node, headings: list[dict[str, Any]]) -> None:
        """Process a heading node and add it to the headings list."""
        level = node.get_heading_level()
        if not level:
            return

        # メモリ制限の最終チェック
        if len(headings) >= self.MAX_HEADINGS:
            self.logger.warning(
                "Maximum heading count reached, skipping remaining headings"
            )
            return

        # タイトル長制限チェック
        title = node.get_text_content()
        if len(title) > self.MAX_TITLE_LENGTH:
            title = title[: self.MAX_TITLE_LENGTH] + "..."
            self.logger.warning("Heading title truncated due to length limit")

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
                "title": title,
                "node": node,
            }
        )

    def _process_nested_content(
        self,
        node: Node,
        headings: list[dict[str, Any]],
        visited_nodes: set,
        max_depth: int,
        depth: int,
    ) -> None:
        """Process nested content within a node."""
        if not hasattr(node, "content") or not node.content:
            return

        try:
            if isinstance(node.content, list):
                self._collect_headings_recursive(
                    node.content, headings, visited_nodes, max_depth, depth + 1
                )
            elif isinstance(node.content, Node):
                self._collect_headings_recursive(
                    [node.content],
                    headings,
                    visited_nodes,
                    max_depth,
                    depth + 1,
                )
        except Exception as e:
            self.logger.warning(f"Error processing nested content: {e}")

    def _build_toc_structure(self, headings: list[dict[str, Any]]) -> list[TOCEntry]:
        """Build hierarchical TOC structure with error handling"""
        if not headings:
            return []

        entries = []
        stack: list[TOCEntry] = []  # Stack to maintain hierarchy

        try:
            for heading in headings:
                try:
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

                except Exception as e:
                    self.logger.warning(
                        "Error creating TOC entry for heading "
                        f"'{heading.get('title', 'Unknown')}': {e}"
                    )
                    continue

            self.logger.info(
                f"Built TOC structure with {len(entries)} top-level entries"
            )
            return entries

        except Exception as e:
            self.logger.error(f"Critical error building TOC structure: {e}")
            return []

    def _generate_toc_html(self, entries: list[TOCEntry]) -> str:
        """Generate HTML for table of contents with error handling"""
        if not entries:
            return ""

        try:
            html_parts = ['<div class="toc">']
            html_parts.append("<h2>目次</h2>")
            html_parts.append('<ul class="toc-list">')

            for entry in entries:
                try:
                    html_parts.append(self._render_toc_entry(entry))
                except Exception as e:
                    self.logger.warning(f"Error rendering TOC entry: {e}")
                    continue

            html_parts.append("</ul>")
            html_parts.append("</div>")

            result = "\n".join(html_parts)
            self.logger.info("TOC HTML generated successfully")
            return result

        except Exception as e:
            self.logger.error(f"Critical error generating TOC HTML: {e}")
            return ""

    def _render_toc_entry(self, entry: TOCEntry, depth: int = 0) -> str:
        """
        Render a single TOC entry and its children with safety limits

        Args:
            entry: TOC entry to render
            depth: Current rendering depth (for recursion control)
        """
        try:
            # 再帰深度制限
            if depth > self.MAX_RECURSION_DEPTH:
                self.logger.warning(
                    "Maximum rendering depth exceeded for entry: " f"{entry.heading_id}"
                )
                return ""

            escaped_title = escape(entry.get_text_content())
            escaped_id = escape(entry.heading_id)

            html_parts = []
            html_parts.append(f'<li class="toc-level-{entry.level}">')
            html_parts.append(f'<a href="#{escaped_id}">{escaped_title}</a>')

            # Render children if any
            if entry.children:
                html_parts.append("<ul>")
                for child in entry.children:
                    try:
                        html_parts.append(self._render_toc_entry(child, depth + 1))
                    except Exception as e:
                        self.logger.warning(f"Error rendering child entry: {e}")
                        continue
                html_parts.append("</ul>")

            html_parts.append("</li>")
            return "\n".join(html_parts)

        except Exception as e:
            self.logger.warning(f"Error rendering TOC entry: {e}")
            return ""

    def should_generate_toc(self, nodes: list[Node]) -> bool:
        """
        Determine if TOC should be generated with error handling

        Args:
            nodes: List of nodes to check

        Returns:
            bool: True if TOC should be generated (automatic generation when 2+ headings)
        """
        try:
            # Check if there are multiple headings for automatic generation
            headings = self._collect_headings(nodes)
            result = len(headings) >= 2
            self.logger.info(
                f"TOC generation decision: {result} "
                f"(found {len(headings)} headings)"
            )
            return result
        except Exception as e:
            self.logger.error(f"Error determining TOC generation: {e}")
            return False

    def get_toc_statistics(self, entries: list[TOCEntry]) -> dict[str, Any]:
        """Get statistics about the TOC structure with error handling"""
        stats = {
            "total_entries": 0,
            "levels_used": set(),
            "max_depth": 0,
            "entries_by_level": {},
        }

        try:

            def analyze_entry(entry: TOCEntry, depth: int = 0) -> None:
                if depth > self.MAX_RECURSION_DEPTH:
                    self.logger.warning("Maximum analysis depth exceeded")
                    return

                try:
                    stats["total_entries"] += 1  # type: ignore
                    stats["levels_used"].add(entry.level)  # type: ignore
                    stats["max_depth"] = max(stats["max_depth"], depth)  # type: ignore

                    if entry.level not in stats["entries_by_level"]:  # type: ignore
                        stats["entries_by_level"][entry.level] = 0  # type: ignore
                    stats["entries_by_level"][entry.level] += 1  # type: ignore

                    for child in entry.children:
                        analyze_entry(child, depth + 1)

                except Exception as e:
                    self.logger.warning(f"Error analyzing entry: {e}")

            for entry in entries:
                analyze_entry(entry)

            stats["levels_used"] = sorted(list(stats["levels_used"]))  # type: ignore
            self.logger.info(
                f"TOC statistics generated: {stats['total_entries']} entries"
            )
            return stats

        except Exception as e:
            self.logger.error(f"Error generating TOC statistics: {e}")
            return stats
