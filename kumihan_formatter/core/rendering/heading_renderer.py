"""Heading rendering functionality extracted from main_renderer.py

This module handles rendering of heading elements (h1-h5) to reduce
the size of main_renderer.py and maintain the 300-line limit.
"""

from ..ast_nodes import Node
from .element_renderer import ElementRenderer


class HeadingRenderer:
    """Handles rendering of heading elements"""

    def __init__(self, element_renderer: ElementRenderer) -> None:
        """Initialize with element renderer instance"""
        self.element_renderer = element_renderer
        self._heading_counter = 0

    @property
    def heading_counter(self) -> int:
        """Get heading counter"""
        return self._heading_counter

    @heading_counter.setter
    def heading_counter(self, value: int) -> None:
        """Set heading counter"""
        self._heading_counter = value

    def render_h1(self, node: Node) -> str:
        """Render h1 heading"""
        self.element_renderer.heading_counter = self._heading_counter
        result = self.element_renderer.render_h1(node)
        self._heading_counter = self.element_renderer.heading_counter
        return result

    def render_h2(self, node: Node) -> str:
        """Render h2 heading"""
        self.element_renderer.heading_counter = self._heading_counter
        result = self.element_renderer.render_h2(node)
        self._heading_counter = self.element_renderer.heading_counter
        return result

    def render_h3(self, node: Node) -> str:
        """Render h3 heading"""
        self.element_renderer.heading_counter = self._heading_counter
        result = self.element_renderer.render_h3(node)
        self._heading_counter = self.element_renderer.heading_counter
        return result

    def render_h4(self, node: Node) -> str:
        """Render h4 heading"""
        self.element_renderer.heading_counter = self._heading_counter
        result = self.element_renderer.render_h4(node)
        self._heading_counter = self.element_renderer.heading_counter
        return result

    def render_h5(self, node: Node) -> str:
        """Render h5 heading"""
        self.element_renderer.heading_counter = self._heading_counter
        result = self.element_renderer.render_h5(node)
        self._heading_counter = self.element_renderer.heading_counter
        return result

    def render_heading(self, node: Node, level: int) -> str:
        """Render heading with ID"""
        self.element_renderer.heading_counter = self._heading_counter
        result = self.element_renderer.render_heading(node, level)
        self._heading_counter = self.element_renderer.heading_counter
        return result

    def render_heading_by_level(self, node: Node) -> str:
        """
        Render heading based on node type (h1-h5)

        Args:
            node: Node with heading type

        Returns:
            str: Rendered HTML
        """
        level_map = {
            "h1": 1,
            "h2": 2,
            "h3": 3,
            "h4": 4,
            "h5": 5,
        }

        if node.type in level_map:
            level = level_map[node.type]
            return self.render_heading(node, level)

        # Fallback to specific methods
        method_map = {
            "h1": self.render_h1,
            "h2": self.render_h2,
            "h3": self.render_h3,
            "h4": self.render_h4,
            "h5": self.render_h5,
        }

        if node.type in method_map:
            return method_map[node.type](node)

        # Default to h1 if type is not recognized
        return self.render_h1(node)

    def reset_counters(self) -> None:
        """Reset heading counter"""
        self._heading_counter = 0
