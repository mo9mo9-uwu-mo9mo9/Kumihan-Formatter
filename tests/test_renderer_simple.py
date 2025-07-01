"""Simplified tests for renderer.py to achieve high coverage

Tests for Issue #351 - Phase 1 priority A (90%+ coverage target)
"""

import pytest
from pathlib import Path
from typing import List, Dict, Any

from kumihan_formatter.renderer import Renderer, render
from kumihan_formatter.core.ast_nodes import Node


class TestRendererBasic:
    """Basic renderer tests with real Node objects"""

    def test_renderer_init_default(self):
        """Test renderer initialization"""
        renderer = Renderer()
        assert renderer.html_renderer is not None
        assert renderer.template_manager is not None
        assert renderer.toc_generator is not None

    def test_renderer_init_with_template_dir(self):
        """Test renderer with custom template directory"""
        renderer = Renderer(Path("/tmp"))
        assert renderer.html_renderer is not None

    def test_render_empty_ast(self):
        """Test rendering empty AST"""
        renderer = Renderer()
        result = renderer.render([])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_simple_paragraph(self):
        """Test rendering simple paragraph"""
        renderer = Renderer()
        node = Node(type="paragraph", content="Hello world")
        result = renderer.render([node])
        assert isinstance(result, str)
        assert "Hello world" in result

    def test_render_with_title(self):
        """Test rendering with title"""
        renderer = Renderer()
        node = Node(type="paragraph", content="Content")
        result = renderer.render([node], title="Test Title")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_with_all_parameters(self):
        """Test rendering with all parameters"""
        renderer = Renderer()
        node = Node(type="paragraph", content="Content")
        result = renderer.render(
            ast=[node],
            config={'test': 'value'},
            template='base',
            title='Test Title',
            source_text='# Source content',
            source_filename='test.txt',
            navigation_html='<nav>Navigation</nav>'
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_multiple_nodes(self):
        """Test rendering multiple nodes"""
        renderer = Renderer()
        nodes = [
            Node(type="paragraph", content="First paragraph"),
            Node(type="paragraph", content="Second paragraph")
        ]
        result = renderer.render(nodes)
        assert isinstance(result, str)
        assert "First paragraph" in result
        assert "Second paragraph" in result

    def test_render_with_toc_node(self):
        """Test rendering with TOC node"""
        renderer = Renderer()
        nodes = [
            Node(type="paragraph", content="Content"),
            Node(type="toc", content="")
        ]
        result = renderer.render(nodes)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_nodes_only(self):
        """Test rendering nodes without template"""
        renderer = Renderer()
        node = Node(type="paragraph", content="Test content")
        result = renderer.render_nodes_only([node])
        assert isinstance(result, str)

    def test_render_nodes_only_empty(self):
        """Test rendering empty nodes without template"""
        renderer = Renderer()
        result = renderer.render_nodes_only([])
        assert isinstance(result, str)

    def test_render_with_custom_context(self):
        """Test rendering with custom context"""
        renderer = Renderer()
        node = Node(type="paragraph", content="Content")
        custom_context = {'custom_var': 'custom_value'}
        result = renderer.render_with_custom_context(
            [node], 'base.html', custom_context
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_toc_data(self):
        """Test getting TOC data"""
        renderer = Renderer()
        node = Node(type="heading", content="Test Heading")
        node.add_attribute("level", 1)
        result = renderer.get_toc_data([node])
        assert isinstance(result, dict)

    def test_get_headings(self):
        """Test getting headings"""
        renderer = Renderer()
        node = Node(type="heading", content="Test Heading")
        node.add_attribute("level", 1)
        result = renderer.get_headings([node])
        assert isinstance(result, list)

    def test_validate_template(self):
        """Test template validation"""
        renderer = Renderer()
        is_valid, error = renderer.validate_template('base.html')
        assert isinstance(is_valid, bool)
        if error is not None:
            assert isinstance(error, str)

    def test_get_available_templates(self):
        """Test getting available templates"""
        renderer = Renderer()
        templates = renderer.get_available_templates()
        assert isinstance(templates, list)

    def test_clear_caches(self):
        """Test clearing caches"""
        renderer = Renderer()
        renderer.clear_caches()  # Should not raise exception

    def test_module_level_render_function(self):
        """Test module-level render function"""
        node = Node(type="paragraph", content="Test content")
        result = render([node])
        assert isinstance(result, str)
        assert "Test content" in result

    def test_module_level_render_empty(self):
        """Test module-level render with empty AST"""
        result = render([])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_module_level_render_with_params(self):
        """Test module-level render with parameters"""
        node = Node(type="paragraph", content="Content")
        result = render(
            [node],
            config={'test': 'value'},
            template='base',
            title='Test'
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_renderer_reuse(self):
        """Test renderer can be reused"""
        renderer = Renderer()
        
        # First render
        node1 = Node(type="paragraph", content="First")
        result1 = renderer.render([node1])
        
        # Second render
        node2 = Node(type="paragraph", content="Second")
        result2 = renderer.render([node2])
        
        assert isinstance(result1, str)
        assert isinstance(result2, str)
        assert "First" in result1
        assert "Second" in result2

    def test_render_with_source_toggle(self):
        """Test rendering with source toggle"""
        renderer = Renderer()
        node = Node(type="paragraph", content="Content")
        result = renderer.render(
            [node],
            source_text="# Source content",
            source_filename="test.md"
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_with_navigation(self):
        """Test rendering with navigation"""
        renderer = Renderer()
        node = Node(type="paragraph", content="Content")
        result = renderer.render(
            [node],
            navigation_html="<nav>Test Nav</nav>"
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_with_config(self):
        """Test rendering with config"""
        renderer = Renderer()
        node = Node(type="paragraph", content="Content")
        result = renderer.render([node], config={'theme': 'dark'})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_with_template(self):
        """Test rendering with specific template"""
        renderer = Renderer()
        node = Node(type="paragraph", content="Content")
        result = renderer.render([node], template='base')
        assert isinstance(result, str)
        assert len(result) > 0

    def test_edge_cases(self):
        """Test various edge cases"""
        renderer = Renderer()
        
        # Empty title
        node = Node(type="paragraph", content="Content")
        result1 = renderer.render([node], title="")
        assert isinstance(result1, str)
        
        # Long title
        result2 = renderer.render([node], title="a" * 1000)
        assert isinstance(result2, str)
        
        # Unicode content
        unicode_node = Node(type="paragraph", content="こんにちは世界 🚀")
        result3 = renderer.render([unicode_node])
        assert isinstance(result3, str)

    def test_custom_context_edge_cases(self):
        """Test custom context edge cases"""
        renderer = Renderer()
        node = Node(type="paragraph", content="Content")
        
        # Empty context
        result1 = renderer.render_with_custom_context([node], 'base.html', {})
        assert isinstance(result1, str)
        
        # Context with None values
        result2 = renderer.render_with_custom_context(
            [node], 'base.html', {'key': None}
        )
        assert isinstance(result2, str)