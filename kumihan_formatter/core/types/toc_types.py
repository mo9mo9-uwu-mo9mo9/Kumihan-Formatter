"""TOCエントリー・基本データ構造

目次のデータ構造とエントリー管理クラス。
"""

from ..ast_nodes import Node


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
        import re

        clean_title = re.sub(r"<[^>]+>", "", self.title)
        return clean_title.strip()
