"""Table of Contents generation for Kumihan-Formatter

This module handles the generation of table of contents from heading elements.
This file now serves as a compatibility wrapper, with main classes moved to toc_main.py
to comply with the 300-line limit.
"""

import re

from ..ast_nodes import Node

# 互換エクスポート
__all__: list[str] = ["TOCEntry", "TOCGenerator"]


class TOCEntry:
    """Represents a single entry in the table of contents"""

    def __init__(self, level: int, title: str, heading_id: str, node: Node):
        self.level = level
        self.title = title
        self.heading_id = heading_id
        self.node = node
        self.children: list["TOCEntry"] = []
        self.parent: "TOCEntry" | None = None

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
        clean_title = re.sub(r"<[^>]+>", "", self.title)
        return clean_title.strip()


class TOCGenerator:
    """Minimal TOC generator (P1)

    入力ノード列から h1〜h5 の見出しを抽出し、階層化した TOCEntry ツリーを構築する。
    """

    SUPPORTED = {"h1", "h2", "h3", "h4", "h5"}

    def generate_from_nodes(self, nodes: list[Node]) -> list[TOCEntry]:
        stack: list[TOCEntry] = []
        roots: list[TOCEntry] = []

        for n in nodes:
            # ノードのレベル判定（type または tag）
            t = getattr(n, "type", None)
            tag = getattr(n, "tag", None)
            heading = None
            if isinstance(t, str) and t in self.SUPPORTED:
                heading = t
            elif isinstance(tag, str) and tag.lower() in self.SUPPORTED:
                heading = tag.lower()
            if not heading:
                continue

            level = int(heading[1])
            title = (
                getattr(n, "content", "")
                if isinstance(getattr(n, "content", ""), str)
                else str(getattr(n, "content", ""))
            )
            entry = TOCEntry(
                level=level,
                title=title,
                heading_id=f"h-{len(roots)+len(stack)+1}",
                node=n,
            )

            # スタックをレベルに合わせて調整
            while stack and stack[-1].level >= level:
                stack.pop()
            if stack:
                stack[-1].add_child(entry)
            else:
                roots.append(entry)
            stack.append(entry)

        return roots
