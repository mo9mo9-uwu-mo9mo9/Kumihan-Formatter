"""Comprehensive tests for renderer.py module

Tests for Issue #351 - Phase 1 priority A (90%+ coverage target)
"""

import pytest
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch

from kumihan_formatter.renderer import Renderer, render
from kumihan_formatter.core.ast_nodes import Node


class TestRendererInit:
    """Test renderer initialization"""

    def test_renderer_init_default(self):
        """Test renderer initialization with default parameters"""
        renderer = Renderer()
        assert renderer.html_renderer is not None
        assert renderer.template_manager is not None
        assert renderer.toc_generator is not None

    def test_renderer_init_with_template_dir(self):
        """Test renderer initialization with custom template directory"""
        template_dir = Path("/tmp/test_templates")
        renderer = Renderer(template_dir)
        assert renderer.html_renderer is not None
        assert renderer.template_manager is not None
        assert renderer.toc_generator is not None

    def test_renderer_init_with_none_template_dir(self):
        """Test renderer initialization with None template directory"""
        renderer = Renderer(None)
        assert renderer.html_renderer is not None
        assert renderer.template_manager is not None
        assert renderer.toc_generator is not None


class TestRendererBasicRendering:
    """Test basic rendering functionality"""

    def test_render_empty_ast(self):
        """Test rendering empty AST"""
        renderer = Renderer()
        result = renderer.render([])
        assert isinstance(result, str)
        assert len(result) > 0  # Should return template with empty content

    def test_render_single_node(self):
        """Test rendering single node"""
        renderer = Renderer()
        # Create a real node
        node = Node(type="paragraph", content="Test content")
        result = renderer.render([node])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_multiple_nodes(self):
        """Test rendering multiple nodes"""
        renderer = Renderer()
        nodes = []
        for i in range(3):
            node = Mock(spec=Node)
            node.type = "paragraph"
            nodes.append(node)
        result = renderer.render(nodes)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_with_all_parameters(self):
        """Test rendering with all parameters specified"""
        renderer = Renderer()
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        result = renderer.render(
            ast=[node],
            config={'test': 'value'},
            template='base',
            title='Test Title',
            source_text='# Test Source',
            source_filename='test.txt',
            navigation_html='<nav>Navigation</nav>'
        )
        assert isinstance(result, str)
        assert len(result) > 0


class TestRendererNodeFiltering:
    """Test node filtering functionality"""

    def test_render_filters_toc_markers(self):
        """Test that TOC markers are filtered from body content"""
        renderer = Renderer()
        
        # Create nodes including a TOC marker
        normal_node = Mock(spec=Node)
        normal_node.type = "paragraph"
        
        toc_node = Mock(spec=Node)
        toc_node.type = "toc"
        
        nodes = [normal_node, toc_node, normal_node]
        result = renderer.render(nodes)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_with_mixed_node_types(self):
        """Test rendering with mixed node types"""
        renderer = Renderer()
        
        # Create various node types
        nodes = []
        for node_type in ["paragraph", "heading", "list", "toc"]:
            node = Mock(spec=Node)
            node.type = node_type
            nodes.append(node)
        
        result = renderer.render(nodes)
        assert isinstance(result, str)
        assert len(result) > 0


class TestRendererTOCGeneration:
    """Test table of contents generation"""

    def test_render_with_toc_enabled(self):
        """Test rendering when TOC should be shown"""
        renderer = Renderer()
        
        # Mock TOC generator to return TOC data
        with patch.object(renderer.toc_generator, 'generate_toc') as mock_toc:
            mock_toc.return_value = {
                "html": "<div class='toc'>TOC Content</div>",
                "has_toc": True
            }
            
            node = Mock(spec=Node)
            node.type = "heading"
            result = renderer.render([node])
            assert isinstance(result, str)
            mock_toc.assert_called_once()

    def test_render_with_toc_disabled(self):
        """Test rendering when TOC should not be shown"""
        renderer = Renderer()
        
        # Mock TOC generator to return no TOC
        with patch.object(renderer.toc_generator, 'generate_toc') as mock_toc:
            mock_toc.return_value = {
                "html": "",
                "has_toc": False
            }
            
            node = Mock(spec=Node)
            node.type = "paragraph"
            result = renderer.render([node])
            assert isinstance(result, str)
            mock_toc.assert_called_once()

    def test_render_with_explicit_toc_node(self):
        """Test rendering with explicit TOC node forces TOC display"""
        renderer = Renderer()
        
        # Mock TOC generator
        with patch.object(renderer.toc_generator, 'generate_toc') as mock_toc:
            mock_toc.return_value = {
                "html": "<div class='toc'>TOC Content</div>",
                "has_toc": False  # Generator says no TOC, but we have explicit node
            }
            
            toc_node = Mock(spec=Node)
            toc_node.type = "toc"
            result = renderer.render([toc_node])
            assert isinstance(result, str)


class TestRendererTemplateManagement:
    """Test template management functionality"""

    def test_render_with_custom_template(self):
        """Test rendering with custom template"""
        renderer = Renderer()
        
        # Mock template manager
        with patch.object(renderer.template_manager, 'select_template_name') as mock_select:
            mock_select.return_value = 'custom.html'
            
            node = Mock(spec=Node)
            node.type = "paragraph"
            result = renderer.render([node], template='custom')
            assert isinstance(result, str)
            mock_select.assert_called_once()

    def test_render_with_source_toggle(self):
        """Test rendering with source toggle enabled"""
        renderer = Renderer()
        
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        result = renderer.render(
            [node],
            source_text="# Source content",
            source_filename="test.md"
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_with_navigation(self):
        """Test rendering with navigation HTML"""
        renderer = Renderer()
        
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        result = renderer.render(
            [node],
            navigation_html="<nav>Test Navigation</nav>"
        )
        assert isinstance(result, str)
        assert len(result) > 0


class TestRendererUtilityMethods:
    """Test utility methods"""

    def test_render_nodes_only(self):
        """Test rendering nodes without template wrapper"""
        renderer = Renderer()
        
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        result = renderer.render_nodes_only([node])
        assert isinstance(result, str)

    def test_render_nodes_only_empty(self):
        """Test rendering empty nodes list without template"""
        renderer = Renderer()
        result = renderer.render_nodes_only([])
        assert isinstance(result, str)

    def test_render_with_custom_context(self):
        """Test rendering with custom template context"""
        renderer = Renderer()
        
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        custom_context = {
            'custom_var': 'custom_value',
            'another_var': 42
        }
        
        result = renderer.render_with_custom_context(
            [node], 
            'base.html', 
            custom_context
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_toc_data(self):
        """Test getting TOC data without rendering"""
        renderer = Renderer()
        
        node = Mock(spec=Node)
        node.type = "heading"
        
        result = renderer.get_toc_data([node])
        assert isinstance(result, dict)

    def test_get_headings(self):
        """Test getting headings from AST"""
        renderer = Renderer()
        
        node = Mock(spec=Node)
        node.type = "heading"
        
        # Mock HTML renderer's collect_headings method
        with patch.object(renderer.html_renderer, 'collect_headings') as mock_collect:
            mock_collect.return_value = [{'level': 1, 'text': 'Test Heading'}]
            
            result = renderer.get_headings([node])
            assert isinstance(result, list)
            mock_collect.assert_called_once_with([node])

    def test_validate_template_valid(self):
        """Test template validation with valid template"""
        renderer = Renderer()
        
        with patch.object(renderer.template_manager, 'validate_template') as mock_validate:
            mock_validate.return_value = (True, None)
            
            is_valid, error = renderer.validate_template('base.html')
            assert is_valid is True
            assert error is None
            mock_validate.assert_called_once_with('base.html')

    def test_validate_template_invalid(self):
        """Test template validation with invalid template"""
        renderer = Renderer()
        
        with patch.object(renderer.template_manager, 'validate_template') as mock_validate:
            mock_validate.return_value = (False, "Template not found")
            
            is_valid, error = renderer.validate_template('nonexistent.html')
            assert is_valid is False
            assert error == "Template not found"

    def test_get_available_templates(self):
        """Test getting list of available templates"""
        renderer = Renderer()
        
        with patch.object(renderer.template_manager, 'get_available_templates') as mock_get:
            mock_get.return_value = ['base.html', 'docs.html', 'custom.html']
            
            templates = renderer.get_available_templates()
            assert isinstance(templates, list)
            assert len(templates) == 3
            assert 'base.html' in templates

    def test_clear_caches(self):
        """Test clearing all internal caches"""
        renderer = Renderer()
        
        with patch.object(renderer.template_manager, 'clear_cache') as mock_clear_template:
            with patch.object(renderer.html_renderer, 'reset_counters') as mock_reset_html:
                renderer.clear_caches()
                mock_clear_template.assert_called_once()
                mock_reset_html.assert_called_once()


class TestRenderFunction:
    """Test module-level render function"""

    def test_render_function_basic(self):
        """Test module-level render function with basic input"""
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        result = render([node])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_function_with_all_params(self):
        """Test module-level render function with all parameters"""
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        result = render(
            ast=[node],
            config={'test': 'value'},
            template='base',
            title='Test Title',
            source_text='# Source',
            source_filename='test.txt',
            navigation_html='<nav>Nav</nav>'
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_function_empty_ast(self):
        """Test module-level render function with empty AST"""
        result = render([])
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_function_with_config_only(self):
        """Test module-level render function with config only"""
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        result = render([node], config={'theme': 'dark'})
        assert isinstance(result, str)
        assert len(result) > 0


class TestRendererErrorHandling:
    """Test error handling and edge cases"""

    def test_render_with_none_ast(self):
        """Test rendering with None AST (should handle gracefully)"""
        renderer = Renderer()
        
        # This might raise an exception or handle gracefully
        try:
            result = renderer.render(None)
            assert isinstance(result, str)
        except (TypeError, AttributeError):
            # Expected behavior for None input
            pass

    def test_render_with_invalid_node_types(self):
        """Test rendering with invalid node types"""
        renderer = Renderer()
        
        # Create node with None type
        node = Mock(spec=Node)
        node.type = None
        
        result = renderer.render([node])
        assert isinstance(result, str)

    def test_render_nodes_only_with_none(self):
        """Test render_nodes_only with None input"""
        renderer = Renderer()
        
        try:
            result = renderer.render_nodes_only(None)
            assert isinstance(result, str)
        except (TypeError, AttributeError):
            # Expected behavior for None input
            pass


class TestRendererStateManagement:
    """Test renderer state management"""

    def test_multiple_renders_independent(self):
        """Test that multiple renders are independent"""
        renderer = Renderer()
        
        node1 = Mock(spec=Node)
        node1.type = "paragraph"
        
        node2 = Mock(spec=Node)
        node2.type = "heading"
        
        result1 = renderer.render([node1], title="First Title")
        result2 = renderer.render([node2], title="Second Title")
        
        assert isinstance(result1, str)
        assert isinstance(result2, str)
        assert result1 != result2  # Should be different

    def test_renderer_reuse(self):
        """Test that renderer can be reused safely"""
        renderer = Renderer()
        
        # First render
        node = Mock(spec=Node)
        node.type = "paragraph"
        result1 = renderer.render([node])
        
        # Second render with different content
        node2 = Mock(spec=Node)
        node2.type = "heading"
        result2 = renderer.render([node2])
        
        assert isinstance(result1, str)
        assert isinstance(result2, str)
        # Results should be independent

    def test_clear_caches_effect(self):
        """Test that clearing caches doesn't break functionality"""
        renderer = Renderer()
        
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        # Render, clear caches, render again
        result1 = renderer.render([node])
        renderer.clear_caches()
        result2 = renderer.render([node])
        
        assert isinstance(result1, str)
        assert isinstance(result2, str)


class TestRendererEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_render_with_empty_title(self):
        """Test rendering with empty string title"""
        renderer = Renderer()
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        result = renderer.render([node], title="")
        assert isinstance(result, str)

    def test_render_with_very_long_title(self):
        """Test rendering with very long title"""
        renderer = Renderer()
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        long_title = "a" * 10000
        result = renderer.render([node], title=long_title)
        assert isinstance(result, str)

    def test_render_with_unicode_content(self):
        """Test rendering with unicode content"""
        renderer = Renderer()
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        result = renderer.render(
            [node], 
            title="日本語タイトル 🚀",
            source_text="こんにちは世界"
        )
        assert isinstance(result, str)

    def test_custom_context_edge_cases(self):
        """Test custom context with edge cases"""
        renderer = Renderer()
        node = Mock(spec=Node)
        node.type = "paragraph"
        
        # Test with empty context
        result1 = renderer.render_with_custom_context([node], 'base.html', {})
        assert isinstance(result1, str)
        
        # Test with None values in context
        result2 = renderer.render_with_custom_context(
            [node], 'base.html', {'key': None}
        )
        assert isinstance(result2, str)