"""Heading collection functionality extracted from main_renderer.py

This module handles heading collection for TOC generation
to reduce the size of main_renderer.py and maintain the 300-line limit.
"""

from typing import Any, List

from ..ast_nodes import Node


class HeadingCollector:
    """Handles collection of headings for TOC generation"""

    MAX_DEPTH = 50  # Prevent infinite recursion

    def __init__(self) -> None:
        """Initialize heading collector"""
        self.heading_counter = 0

    def collect_headings(
        self, nodes: list[Node], depth: int = 0
    ) -> List[dict[str, Any]]:
        """
        Collect all headings from nodes for TOC generation

        Args:
            nodes: List of nodes to search
            depth: Current recursion depth (prevents infinite recursion)

        Returns:
            list[Dict]: List of heading information
        """
        headings: List[dict[str, Any]] = []

        if depth > self.MAX_DEPTH:
            return headings

        for node in nodes:
            if isinstance(node, Node):
                if node.is_heading():
                    level = node.get_heading_level()
                    if level:
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
                    child_headings = self.collect_headings(node.content, depth + 1)
                    headings.extend(child_headings)

        return headings

    def reset_counters(self) -> None:
        """Reset internal counters"""
        self.heading_counter = 0
