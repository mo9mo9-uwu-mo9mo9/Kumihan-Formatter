"""HTML rendering utilities for Kumihan-Formatter

This module handles the conversion of AST nodes to HTML elements.
"""

import re
from typing import List, Dict, Any, Optional
from html import escape

from .ast_nodes import Node


class HTMLRenderer:
    """Converts AST nodes to HTML"""
    
    # Nesting order for compound elements (outer to inner)
    NESTING_ORDER = [
        'details',  # 折りたたみ, ネタバレ
        'div',      # 枠線, ハイライト  
        'h1', 'h2', 'h3', 'h4', 'h5',  # 見出し
        'strong',   # 太字
        'em'        # イタリック
    ]
    
    def __init__(self):
        """Initialize HTML renderer"""
        self.heading_counter = 0
    
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
        tag = node.type
        content = self._render_content(node.content)
        attributes = self._render_attributes(node.attributes)
        
        if attributes:
            return f'<{tag} {attributes}>{content}</{tag}>'
        else:
            return f'<{tag}>{content}</{tag}>'
    
    def _render_p(self, node: Node) -> str:
        """Render paragraph node"""
        content = self._render_content(node.content, 0)
        return f'<p>{content}</p>'
    
    def _render_strong(self, node: Node) -> str:
        """Render strong (bold) node"""
        content = self._render_content(node.content, 0)
        return f'<strong>{content}</strong>'
    
    def _render_em(self, node: Node) -> str:
        """Render emphasis (italic) node"""
        content = self._render_content(node.content, 0)
        return f'<em>{content}</em>'
    
    def _render_div(self, node: Node) -> str:
        """Render div node"""
        content = self._render_content(node.content, 0)
        attributes = self._render_attributes(node.attributes)
        
        if attributes:
            return f'<div {attributes}>{content}</div>'
        else:
            return f'<div>{content}</div>'
    
    def _render_h1(self, node: Node) -> str:
        """Render h1 heading"""
        return self._render_heading(node, 1)
    
    def _render_h2(self, node: Node) -> str:
        """Render h2 heading"""
        return self._render_heading(node, 2)
    
    def _render_h3(self, node: Node) -> str:
        """Render h3 heading"""
        return self._render_heading(node, 3)
    
    def _render_h4(self, node: Node) -> str:
        """Render h4 heading"""
        return self._render_heading(node, 4)
    
    def _render_h5(self, node: Node) -> str:
        """Render h5 heading"""
        return self._render_heading(node, 5)
    
    def _render_heading(self, node: Node, level: int) -> str:
        """Render heading with ID"""
        content = self._render_content(node.content, 0)
        
        # Generate heading ID if not present
        heading_id = node.get_attribute('id')
        if not heading_id:
            self.heading_counter += 1
            heading_id = f'heading-{self.heading_counter}'
            node.add_attribute('id', heading_id)
        
        attributes = self._render_attributes(node.attributes)
        tag = f'h{level}'
        
        if attributes:
            return f'<{tag} {attributes}>{content}</{tag}>'
        else:
            return f'<{tag}>{content}</{tag}>'
    
    def _render_ul(self, node: Node) -> str:
        """Render unordered list"""
        items = []
        if isinstance(node.content, list):
            for item in node.content:
                if isinstance(item, Node) and item.type == 'li':
                    items.append(self.render_node(item))
        
        items_html = '\n'.join(items)
        return f'<ul>\n{items_html}\n</ul>'
    
    def _render_ol(self, node: Node) -> str:
        """Render ordered list"""
        items = []
        if isinstance(node.content, list):
            for item in node.content:
                if isinstance(item, Node) and item.type == 'li':
                    items.append(self.render_node(item))
        
        items_html = '\n'.join(items)
        return f'<ol>\n{items_html}\n</ol>'
    
    def _render_li(self, node: Node) -> str:
        """Render list item"""
        content = self._render_content(node.content, 0)
        return f'<li>{content}</li>'
    
    def _render_details(self, node: Node) -> str:
        """Render details/summary element"""
        content = self._render_content(node.content, 0)
        summary = node.get_attribute('summary', '詳細を表示')
        
        return f'<details><summary>{escape(summary)}</summary>{content}</details>'
    
    def _render_pre(self, node: Node) -> str:
        """Render preformatted text"""
        # For code blocks, preserve whitespace and escape HTML
        if isinstance(node.content, str):
            content = escape(node.content)
        else:
            content = self._render_content(node.content, 0)
        
        attributes = self._render_attributes(node.attributes)
        
        if attributes:
            return f'<pre {attributes}>{content}</pre>'
        else:
            return f'<pre>{content}</pre>'
    
    def _render_code(self, node: Node) -> str:
        """Render inline code"""
        if isinstance(node.content, str):
            content = escape(node.content)
        else:
            content = self._render_content(node.content, 0)
        
        attributes = self._render_attributes(node.attributes)
        
        if attributes:
            return f'<code {attributes}>{content}</code>'
        else:
            return f'<code>{content}</code>'
    
    def _render_image(self, node: Node) -> str:
        """Render image element"""
        filename = node.content if isinstance(node.content, str) else str(node.content)
        alt_text = node.get_attribute('alt', '')
        
        # Construct image path
        src = f'images/{filename}'
        
        if alt_text:
            return f'<img src="{escape(src)}" alt="{escape(alt_text)}" />'
        else:
            return f'<img src="{escape(src)}" />'
    
    def _render_error(self, node: Node) -> str:
        """Render error node"""
        content = escape(str(node.content))
        line_number = node.get_attribute('line')
        
        error_text = f'[ERROR: {content}]'
        if line_number:
            error_text = f'[ERROR (Line {line_number}): {content}]'
        
        return f'<span style="background-color:#ffe6e6; color:#d32f2f; padding:2px 4px; border-radius:3px;">{error_text}</span>'
    
    def _render_toc(self, node: Node) -> str:
        """Render table of contents marker (should be handled by TOC generator)"""
        return '<!-- TOC placeholder -->'
    
    def _render_content(self, content: Any, depth: int = 0) -> str:
        """Render node content (recursive)"""
        max_depth = 100  # Prevent infinite recursion
        
        if depth > max_depth:
            return '[ERROR: Maximum recursion depth reached]'
            
        if content is None:
            return ''
        elif isinstance(content, str):
            return self._process_text_content(content)
        elif isinstance(content, Node):
            # Handle single Node objects
            return self._render_node_with_depth(content, depth + 1)
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, Node):
                    parts.append(self._render_node_with_depth(item, depth + 1))
                elif isinstance(item, str):
                    parts.append(self._process_text_content(item))
                else:
                    parts.append(self._process_text_content(str(item)))
            return ''.join(parts)
        else:
            return self._process_text_content(str(content))
    
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
        tag = node.type
        content = self._render_content(node.content, depth)
        attributes = self._render_attributes(node.attributes)
        
        if attributes:
            return f'<{tag} {attributes}>{content}</{tag}>'
        else:
            return f'<{tag}>{content}</{tag}>'
    
    def _process_text_content(self, text: str) -> str:
        """
        Process text content, converting newlines to <br> tags
        
        Args:
            text: Raw text content
        
        Returns:
            str: Processed HTML with proper line breaks
        """
        # Escape HTML entities first
        escaped_text = escape(text)
        
        # Convert newlines to <br> tags
        # Use regex to handle various line ending types
        processed_text = re.sub(r'\r?\n', '<br>', escaped_text)
        
        return processed_text
    
    def _render_attributes(self, attributes: Dict[str, Any]) -> str:
        """Render HTML attributes"""
        if not attributes:
            return ''
        
        attr_parts = []
        for key, value in attributes.items():
            if value is not None:
                escaped_value = escape(str(value))
                attr_parts.append(f'{key}="{escaped_value}"')
        
        return ' '.join(attr_parts)
    
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


class CompoundElementRenderer:
    """Renderer for compound elements with multiple keywords"""
    
    def __init__(self, html_renderer: HTMLRenderer):
        self.html_renderer = html_renderer
    
    def render_compound_element(self, keywords: List[str], content: str, attributes: Dict[str, Any]) -> str:
        """
        Render element with multiple keywords applied
        
        Args:
            keywords: List of keywords to apply
            content: Content to render
            attributes: Additional attributes
        
        Returns:
            str: Rendered HTML with nested elements
        """
        # Sort keywords by nesting order
        sorted_keywords = self._sort_by_nesting_order(keywords)
        
        # Build nested HTML from inner to outer
        current_html = self.html_renderer._process_text_content(content)
        
        for keyword in reversed(sorted_keywords):
            current_html = self._wrap_with_keyword(current_html, keyword, attributes)
        
        return current_html
    
    def _sort_by_nesting_order(self, keywords: List[str]) -> List[str]:
        """Sort keywords by their nesting order"""
        # Map keywords to their HTML tags
        keyword_to_tag = {
            '折りたたみ': 'details',
            'ネタバレ': 'details',
            '枠線': 'div',
            'ハイライト': 'div',
            '見出し1': 'h1',
            '見出し2': 'h2', 
            '見出し3': 'h3',
            '見出し4': 'h4',
            '見出し5': 'h5',
            '太字': 'strong',
            'イタリック': 'em'
        }
        
        def get_tag_priority(keyword: str) -> int:
            tag = keyword_to_tag.get(keyword, 'span')
            try:
                return self.html_renderer.NESTING_ORDER.index(tag)
            except ValueError:
                return 999
        
        return sorted(keywords, key=get_tag_priority)
    
    def _wrap_with_keyword(self, content: str, keyword: str, attributes: Dict[str, Any]) -> str:
        """Wrap content with HTML for a specific keyword"""
        if keyword == '太字':
            return f'<strong>{content}</strong>'
        elif keyword == 'イタリック':
            return f'<em>{content}</em>'
        elif keyword == '枠線':
            return f'<div class="box">{content}</div>'
        elif keyword == 'ハイライト':
            style = ''
            if 'color' in attributes:
                color = attributes['color']
                if not color.startswith('#'):
                    color = '#' + color
                style = f' style="background-color:{color}"'
            return f'<div class="highlight"{style}>{content}</div>'
        elif keyword.startswith('見出し'):
            level = keyword[-1]
            return f'<h{level}>{content}</h{level}>'
        elif keyword == '折りたたみ':
            return f'<details><summary>詳細を表示</summary>{content}</details>'
        elif keyword == 'ネタバレ':
            return f'<details><summary>ネタバレを表示</summary>{content}</details>'
        else:
            # Fallback
            return f'<span class="{keyword}">{content}</span>'