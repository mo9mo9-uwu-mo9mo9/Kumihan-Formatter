"""Main HTML renderer for Kumihan-Formatter

This module provides the main HTMLRenderer class that coordinates
all specialized renderers and maintains backward compatibility.
"""

from typing import List, Dict, Any
from html import escape

from ..ast_nodes import Node
from .element_renderer import ElementRenderer
from .compound_renderer import CompoundElementRenderer
from .html_utils import process_text_content
from .html_formatter import HTMLFormatter


class HTMLRenderer:
    """Main HTML renderer that coordinates specialized renderers"""
    
    # Maintain the original nesting order for backward compatibility
    NESTING_ORDER = [
        'details',  # 折りたたみ, ネタバレ
        'div',      # 枠線, ハイライト  
        'h1', 'h2', 'h3', 'h4', 'h5',  # 見出し
        'strong',   # 太字
        'em'        # イタリック
    ]
    
    def __init__(self):
        """Initialize HTML renderer with specialized renderers"""
        self.element_renderer = ElementRenderer()
        self.compound_renderer = CompoundElementRenderer()
        self.formatter = HTMLFormatter()
        self.heading_counter = 0
        
        # Inject this main renderer into element renderer for content processing
        self.element_renderer._main_renderer = self
    
    def render_nodes(self, nodes: List[Node]) -> str:
        """
        Render a list of nodes to HTML
        
        Args:
            nodes: List of AST nodes to render
        
        Returns:
            str: Generated HTML
        """
        html_parts = []
        
        for node in nodes:
            html = self.render_node(node)
            if html:
                html_parts.append(html)
        
        return '\n'.join(html_parts)
    
    def render_node(self, node: Node) -> str:
        """
        Render a single node to HTML
        
        Args:
            node: AST node to render
        
        Returns:
            str: Generated HTML for the node
        """
        if not isinstance(node, Node):
            return escape(str(node))
        
        # Route to specific rendering method
        renderer_method = getattr(self, f'_render_{node.type}', self._render_generic)
        return renderer_method(node)
    
    def _render_generic(self, node: Node) -> str:
        """Generic node renderer"""
        return self.element_renderer.render_generic(node)
    
    def _render_p(self, node: Node) -> str:
        """Render paragraph node"""
        return self.element_renderer.render_paragraph(node)
    
    def _render_strong(self, node: Node) -> str:
        """Render strong (bold) node"""
        return self.element_renderer.render_strong(node)
    
    def _render_em(self, node: Node) -> str:
        """Render emphasis (italic) node"""
        return self.element_renderer.render_emphasis(node)
    
    def _render_div(self, node: Node) -> str:
        """Render div node"""
        return self.element_renderer.render_div(node)
    
    def _render_h1(self, node: Node) -> str:
        """Render h1 heading"""
        # Sync heading counter with element renderer
        self.element_renderer.heading_counter = self.heading_counter
        result = self.element_renderer.render_h1(node)
        self.heading_counter = self.element_renderer.heading_counter
        return result
    
    def _render_h2(self, node: Node) -> str:
        """Render h2 heading"""
        # Sync heading counter with element renderer
        self.element_renderer.heading_counter = self.heading_counter
        result = self.element_renderer.render_h2(node)
        self.heading_counter = self.element_renderer.heading_counter
        return result
    
    def _render_h3(self, node: Node) -> str:
        """Render h3 heading"""
        # Sync heading counter with element renderer
        self.element_renderer.heading_counter = self.heading_counter
        result = self.element_renderer.render_h3(node)
        self.heading_counter = self.element_renderer.heading_counter
        return result
    
    def _render_h4(self, node: Node) -> str:
        """Render h4 heading"""
        # Sync heading counter with element renderer
        self.element_renderer.heading_counter = self.heading_counter
        result = self.element_renderer.render_h4(node)
        self.heading_counter = self.element_renderer.heading_counter
        return result
    
    def _render_h5(self, node: Node) -> str:
        """Render h5 heading"""
        # Sync heading counter with element renderer
        self.element_renderer.heading_counter = self.heading_counter
        result = self.element_renderer.render_h5(node)
        self.heading_counter = self.element_renderer.heading_counter
        return result
    
    def _render_heading(self, node: Node, level: int) -> str:
        """Render heading with ID"""
        # Sync heading counter with element renderer
        self.element_renderer.heading_counter = self.heading_counter
        result = self.element_renderer.render_heading(node, level)
        self.heading_counter = self.element_renderer.heading_counter
        return result
    
    def _render_ul(self, node: Node) -> str:
        """Render unordered list"""
        return self.element_renderer.render_unordered_list(node)
    
    def _render_ol(self, node: Node) -> str:
        """Render ordered list"""
        return self.element_renderer.render_ordered_list(node)
    
    def _render_li(self, node: Node) -> str:
        """Render list item"""
        return self.element_renderer.render_list_item(node)
    
    def _render_details(self, node: Node) -> str:
        """Render details/summary element"""
        return self.element_renderer.render_details(node)
    
    def _render_pre(self, node: Node) -> str:
        """Render preformatted text"""
        return self.element_renderer.render_preformatted(node)
    
    def _render_code(self, node: Node) -> str:
        """Render inline code"""
        return self.element_renderer.render_code(node)
    
    def _render_image(self, node: Node) -> str:
        """Render image element"""
        return self.element_renderer.render_image(node)
    
    def _render_error(self, node: Node) -> str:
        """Render error node"""
        return self.element_renderer.render_error(node)
    
    def _render_toc(self, node: Node) -> str:
        """Render table of contents marker"""
        return self.element_renderer.render_toc_placeholder(node)
    
    def _render_content(self, content: Any, depth: int = 0) -> str:
        """Render node content (recursive)"""
        max_depth = 100  # Prevent infinite recursion
        
        if depth > max_depth:
            return '[ERROR: Maximum recursion depth reached]'
            
        if content is None:
            return ''
        elif isinstance(content, str):
            return process_text_content(content)
        elif isinstance(content, Node):
            # Handle single Node objects
            return self._render_node_with_depth(content, depth + 1)
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, Node):
                    parts.append(self._render_node_with_depth(item, depth + 1))
                elif isinstance(item, str):
                    parts.append(process_text_content(item))
                else:
                    parts.append(process_text_content(str(item)))
            return ''.join(parts)
        else:
            return process_text_content(str(content))
    
    def _render_node_with_depth(self, node: Node, depth: int = 0) -> str:
        """Render a single node with depth tracking"""
        max_depth = 100  # Prevent infinite recursion
        
        if depth > max_depth:
            return '[ERROR: Maximum recursion depth reached]'
            
        if not isinstance(node, Node):
            return escape(str(node))
        
        # Route to specific rendering method
        renderer_method = getattr(self, f'_render_{node.type}', self._render_generic_with_depth)
        if renderer_method == self._render_generic:
            return self._render_generic_with_depth(node, depth)
        else:
            return renderer_method(node)
    
    def _render_generic_with_depth(self, node: Node, depth: int = 0) -> str:
        """Generic node renderer with depth tracking"""
        return self.element_renderer.render_generic(node)
    
    def _process_text_content(self, text: str) -> str:
        """Process text content - delegate to html_utils"""
        return process_text_content(text)
    
    def _contains_html_tags(self, text: str) -> bool:
        """Check if text contains HTML tags - delegate to html_utils"""
        from .html_utils import contains_html_tags
        return contains_html_tags(text)
    
    def _render_attributes(self, attributes: Dict[str, Any]) -> str:
        """Render HTML attributes - delegate to html_utils"""
        from .html_utils import render_attributes
        return render_attributes(attributes)
    
    def collect_headings(self, nodes: List[Node], depth: int = 0) -> List[Dict[str, Any]]:
        """
        Collect all headings from nodes for TOC generation
        
        Args:
            nodes: List of nodes to search
            depth: Current recursion depth (prevents infinite recursion)
        
        Returns:
            List[Dict]: List of heading information
        """
        headings = []
        max_depth = 50  # Prevent infinite recursion
        
        if depth > max_depth:
            return headings
        
        for node in nodes:
            if isinstance(node, Node):
                if node.is_heading():
                    level = node.get_heading_level()
                    if level:
                        heading_id = node.get_attribute('id')
                        if not heading_id:
                            self.heading_counter += 1
                            heading_id = f'heading-{self.heading_counter}'
                            node.add_attribute('id', heading_id)
                        
                        headings.append({
                            'level': level,
                            'id': heading_id,
                            'title': node.get_text_content(),
                            'node': node
                        })
                
                # Recursively search in content with depth tracking
                if isinstance(node.content, list):
                    child_headings = self.collect_headings(node.content, depth + 1)
                    headings.extend(child_headings)
        
        return headings
    
    def reset_counters(self) -> None:
        """Reset internal counters"""
        self.heading_counter = 0
        self.element_renderer.reset_counters()


# Module-level function for backward compatibility
def render_single_node(node: Node, depth: int = 0) -> str:
    """
    Render a single node (used by element_renderer for recursive calls)
    
    Args:
        node: Node to render
        depth: Current recursion depth
    
    Returns:
        str: Rendered HTML
    """
    # Create a temporary renderer instance for recursive calls
    renderer = HTMLRenderer()
    return renderer._render_node_with_depth(node, depth)


# Maintain the original CompoundElementRenderer class for backward compatibility
CompoundElementRenderer = CompoundElementRenderer