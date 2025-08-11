"""Table of Contents generation for Kumihan-Formatter

This module handles the generation of table of contents from heading elements.
This file now serves as a compatibility wrapper, with main classes moved to toc_main.py
to comply with the 300-line limit.
"""

from __future__ import annotations

import re

from .ast_nodes import Node

# Re-export for compatibility
from .toc_generator_main import TOCGenerator

__all__ = ["TOCGenerator"]


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
