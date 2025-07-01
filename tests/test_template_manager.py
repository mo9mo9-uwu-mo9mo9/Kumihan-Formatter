"""Comprehensive tests for template_manager.py module

Tests for Issue #351 - Phase 2 priority B (80%+ coverage target)
"""

import pytest
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
from jinja2 import Template
from jinja2.exceptions import TemplateNotFound

from kumihan_formatter.core.template_manager import TemplateManager, RenderContext, TemplateValidator


class TestTemplateManagerInit:
    """Test TemplateManager initialization"""

    def test_init_default_template_dir(self):
        """Test initialization with default template directory"""
        manager = TemplateManager()
        assert manager.template_dir is not None
        assert isinstance(manager.template_dir, Path)
        assert manager.env is not None

    def test_init_custom_template_dir(self):
        """Test initialization with custom template directory"""
        custom_dir = Path("/tmp/custom_templates")
        manager = TemplateManager(custom_dir)
        assert manager.template_dir == custom_dir
        assert manager.env is not None

    def test_init_none_template_dir(self):
        """Test initialization explicitly with None"""
        manager = TemplateManager(None)
        assert manager.template_dir is not None
        assert "templates" in str(manager.template_dir)

    def test_template_cache_initialized(self):
        """Test that template cache is initialized"""
        manager = TemplateManager()
        assert hasattr(manager, '_template_cache')
        assert isinstance(manager._template_cache, dict)

    def test_custom_filters_registered(self):
        """Test that custom filters are registered"""
        manager = TemplateManager()
        assert 'safe_html' in manager.env.filters
        assert 'truncate_words' in manager.env.filters
        assert 'extract_text' in manager.env.filters
        assert 'format_toc_level' in manager.env.filters


class TestGetTemplate:
    """Test get_template method"""

    def test_get_template_cached(self):
        """Test getting template from cache"""
        manager = TemplateManager()
        mock_template = Mock(spec=Template)
        manager._template_cache['test.html'] = mock_template
        
        result = manager.get_template('test.html')
        assert result is mock_template

    def test_get_template_not_cached(self):
        """Test getting template not in cache"""
        manager = TemplateManager()
        
        with patch.object(manager.env, 'get_template') as mock_get:
            mock_template = Mock(spec=Template)
            mock_get.return_value = mock_template
            
            result = manager.get_template('new.html')
            assert result is mock_template
            assert 'new.html' in manager._template_cache
            mock_get.assert_called_once_with('new.html')

    def test_get_template_error(self):
        """Test getting non-existent template"""
        manager = TemplateManager()
        
        with patch.object(manager.env, 'get_template') as mock_get:
            mock_get.side_effect = TemplateNotFound('not found')
            
            with pytest.raises(TemplateNotFound):
                manager.get_template('nonexistent.html')


class TestRenderTemplate:
    """Test render_template method"""

    def test_render_template_basic(self):
        """Test basic template rendering"""
        manager = TemplateManager()
        mock_template = Mock(spec=Template)
        mock_template.render.return_value = '<html>Test</html>'
        
        with patch.object(manager, 'get_template') as mock_get:
            mock_get.return_value = mock_template
            
            result = manager.render_template('test.html', {'title': 'Test'})
            assert result == '<html>Test</html>'
            mock_template.render.assert_called_once_with({'title': 'Test'})

    def test_render_template_empty_context(self):
        """Test rendering with empty context"""
        manager = TemplateManager()
        mock_template = Mock(spec=Template)
        mock_template.render.return_value = '<html></html>'
        
        with patch.object(manager, 'get_template') as mock_get:
            mock_get.return_value = mock_template
            
            result = manager.render_template('test.html', {})
            assert result == '<html></html>'
            mock_template.render.assert_called_once_with({})

    def test_render_template_complex_context(self):
        """Test rendering with complex context"""
        manager = TemplateManager()
        mock_template = Mock(spec=Template)
        mock_template.render.return_value = '<html>Complex</html>'
        
        context = {
            'title': 'Complex',
            'data': [1, 2, 3],
            'nested': {'key': 'value'}
        }
        
        with patch.object(manager, 'get_template') as mock_get:
            mock_get.return_value = mock_template
            
            result = manager.render_template('test.html', context)
            assert result == '<html>Complex</html>'
            mock_template.render.assert_called_once_with(context)


class TestSelectTemplateName:
    """Test select_template_name method"""

    def test_select_template_with_source_text(self):
        """Test template selection with source text"""
        manager = TemplateManager()
        result = manager.select_template_name(source_text="# Source", template=None)
        assert result == 'base-with-source-toggle.html.j2'

    def test_select_template_explicit(self):
        """Test template selection with explicit template"""
        manager = TemplateManager()
        result = manager.select_template_name(source_text=None, template='custom')
        assert result == 'custom'

    def test_select_template_default(self):
        """Test default template selection"""
        manager = TemplateManager()
        result = manager.select_template_name(source_text=None, template=None)
        assert result == 'base.html.j2'

    def test_select_template_priority(self):
        """Test template selection priority"""
        manager = TemplateManager()
        # Explicit template overrides source text
        result = manager.select_template_name(source_text="# Source", template='custom')
        assert result == 'custom'


class TestGetAvailableTemplates:
    """Test get_available_templates method"""

    def test_get_available_templates(self):
        """Test getting list of available templates"""
        manager = TemplateManager()
        
        # Mock the template directory listing
        with patch('pathlib.Path.glob') as mock_glob:
            mock_files = [
                Path('test1.html'),
                Path('test2.html.j2'),
                Path('subdir/test3.html'),
                Path('not_template.txt')
            ]
            mock_glob.return_value = mock_files
            
            with patch('pathlib.Path.is_file') as mock_is_file:
                mock_is_file.return_value = True
                
                templates = manager.get_available_templates()
                assert isinstance(templates, list)

    def test_get_available_templates_empty(self):
        """Test getting templates from empty directory"""
        manager = TemplateManager()
        
        with patch('pathlib.Path.glob') as mock_glob:
            mock_glob.return_value = []
            
            templates = manager.get_available_templates()
            assert templates == []


class TestValidateTemplate:
    """Test validate_template method"""

    def test_validate_template_valid(self):
        """Test validating valid template"""
        manager = TemplateManager()
        
        with patch.object(manager, 'get_template') as mock_get:
            mock_template = Mock(spec=Template)
            mock_get.return_value = mock_template
            
            is_valid, error = manager.validate_template('test.html')
            assert is_valid is True
            assert error is None

    def test_validate_template_not_found(self):
        """Test validating non-existent template"""
        manager = TemplateManager()
        
        with patch.object(manager, 'get_template') as mock_get:
            mock_get.side_effect = TemplateNotFound('not found')
            
            is_valid, error = manager.validate_template('nonexistent.html')
            assert is_valid is False
            assert 'not found' in error

    def test_validate_template_other_error(self):
        """Test validating template with other error"""
        manager = TemplateManager()
        
        with patch.object(manager, 'get_template') as mock_get:
            mock_get.side_effect = Exception('Syntax error')
            
            is_valid, error = manager.validate_template('error.html')
            assert is_valid is False
            assert 'Syntax error' in error


class TestClearCache:
    """Test clear_cache method"""

    def test_clear_cache(self):
        """Test clearing template cache"""
        manager = TemplateManager()
        manager._template_cache = {'test.html': Mock(), 'other.html': Mock()}
        
        manager.clear_cache()
        assert len(manager._template_cache) == 0


class TestCustomFilters:
    """Test custom Jinja2 filters"""

    def test_safe_html_filter(self):
        """Test safe_html filter"""
        manager = TemplateManager()
        filter_func = manager.env.filters['safe_html']
        
        result = filter_func('<p>Test</p>')
        assert str(result) == '<p>Test</p>'

    def test_truncate_words_filter(self):
        """Test truncate_words filter"""
        manager = TemplateManager()
        filter_func = manager.env.filters['truncate_words']
        
        # Test default truncation
        text = "This is a very long text that should be truncated"
        result = filter_func(text, 5)
        assert "..." in result
        
        # Test custom suffix
        result = filter_func(text, 5, "…")
        assert "…" in result

    def test_extract_text_filter(self):
        """Test extract_text filter"""
        manager = TemplateManager()
        filter_func = manager.env.filters['extract_text']
        
        # Test string content
        assert filter_func("Simple text") == "Simple text"
        
        # Test dict with 'text' key
        assert filter_func({'text': 'Dict text'}) == 'Dict text'
        
        # Test dict with 'content' key
        assert filter_func({'content': 'Dict content'}) == 'Dict content'
        
        # Test other types
        assert filter_func(123) == ""
        assert filter_func(None) == ""

    def test_format_toc_level_filter(self):
        """Test format_toc_level filter"""
        manager = TemplateManager()
        filter_func = manager.env.filters['format_toc_level']
        
        assert filter_func(1) == "toc-level-1"
        assert filter_func(2) == "toc-level-2"
        assert filter_func(3) == "toc-level-3"


class TestRenderContext:
    """Test RenderContext builder class"""

    def test_render_context_init(self):
        """Test RenderContext initialization"""
        context = RenderContext()
        assert context._context == {}

    def test_render_context_title(self):
        """Test setting title"""
        context = RenderContext()
        result = context.title("Test Title")
        assert result is context  # Fluent interface
        assert context._context['title'] == "Test Title"

    def test_render_context_body_content(self):
        """Test setting body content"""
        context = RenderContext()
        result = context.body_content("<p>Body</p>")
        assert result is context
        assert context._context['body_content'] == "<p>Body</p>"

    def test_render_context_toc_html(self):
        """Test setting TOC HTML"""
        context = RenderContext()
        result = context.toc_html("<nav>TOC</nav>")
        assert result is context
        assert context._context['toc_html'] == "<nav>TOC</nav>"

    def test_render_context_has_toc(self):
        """Test setting has_toc flag"""
        context = RenderContext()
        result = context.has_toc(True)
        assert result is context
        assert context._context['has_toc'] is True

    def test_render_context_source_toggle(self):
        """Test setting source toggle"""
        context = RenderContext()
        result = context.source_toggle("# Source", "test.md")
        assert result is context
        assert context._context['has_source_toggle'] is True
        assert context._context['source_text'] == "# Source"
        assert context._context['source_filename'] == "test.md"

    def test_render_context_navigation(self):
        """Test setting navigation"""
        context = RenderContext()
        result = context.navigation("<nav>Nav</nav>")
        assert result is context
        assert context._context['navigation_html'] == "<nav>Nav</nav>"

    def test_render_context_css_vars(self):
        """Test setting CSS variables"""
        context = RenderContext()
        css_vars = {'--primary': '#000', '--secondary': '#fff'}
        result = context.css_vars(css_vars)
        assert result is context
        assert context._context['css_vars'] == css_vars

    def test_render_context_custom(self):
        """Test setting custom values"""
        context = RenderContext()
        result = context.custom('custom_key', 'custom_value')
        assert result is context
        assert context._context['custom_key'] == 'custom_value'

    def test_render_context_metadata(self):
        """Test setting metadata"""
        context = RenderContext()
        result = context.metadata(
            author="Test Author",
            description="Test Description",
            keywords="test, keywords"
        )
        assert result is context
        assert context._context['metadata']['author'] == "Test Author"
        assert context._context['metadata']['description'] == "Test Description"
        assert context._context['metadata']['keywords'] == "test, keywords"

    def test_render_context_build(self):
        """Test building final context"""
        context = RenderContext()
        context.title("Test").body_content("Body").has_toc(True)
        
        result = context.build()
        assert isinstance(result, dict)
        assert result['title'] == "Test"
        assert result['body_content'] == "Body"
        assert result['has_toc'] is True

    def test_render_context_fluent_interface(self):
        """Test fluent interface chaining"""
        context = (RenderContext()
                  .title("Test")
                  .body_content("Body")
                  .toc_html("TOC")
                  .has_toc(True)
                  .custom('key', 'value'))
        
        result = context.build()
        assert result['title'] == "Test"
        assert result['body_content'] == "Body"
        assert result['toc_html'] == "TOC"
        assert result['has_toc'] is True
        assert result['key'] == 'value'


class TestTemplateValidator:
    """Test TemplateValidator class"""

    def test_validator_init(self):
        """Test TemplateValidator initialization"""
        manager = TemplateManager()
        validator = TemplateValidator(manager)
        assert validator.template_manager is manager

    def test_validate_all_templates(self):
        """Test validating all templates"""
        manager = TemplateManager()
        validator = TemplateValidator(manager)
        
        with patch.object(manager, 'get_available_templates') as mock_get_available:
            mock_get_available.return_value = ['test1.html', 'test2.html']
            
            with patch.object(manager, 'validate_template') as mock_validate:
                mock_validate.side_effect = [
                    (True, None),
                    (False, "Error")
                ]
                
                results = validator.validate_all_templates()
                assert 'test1.html' in results
                assert results['test1.html'] == (True, None)
                assert 'test2.html' in results
                assert results['test2.html'] == (False, "Error")

    def test_check_required_templates(self):
        """Test checking required templates"""
        manager = TemplateManager()
        validator = TemplateValidator(manager)
        
        with patch.object(manager, 'get_available_templates') as mock_get_available:
            mock_get_available.return_value = ['base.html.j2', 'docs.html.j2']
            
            results = validator.check_required_templates()
            assert 'base.html.j2' in results
            assert results['base.html.j2'] is True
            assert 'base-with-source-toggle.html.j2' in results
            assert results['base-with-source-toggle.html.j2'] is False


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_template_manager_with_nonexistent_dir(self):
        """Test initialization with non-existent directory"""
        nonexistent = Path("/totally/nonexistent/path")
        manager = TemplateManager(nonexistent)
        assert manager.template_dir == nonexistent

    def test_render_template_with_none_context(self):
        """Test rendering with None context"""
        manager = TemplateManager()
        mock_template = Mock(spec=Template)
        mock_template.render.return_value = '<html></html>'
        
        with patch.object(manager, 'get_template') as mock_get:
            mock_get.return_value = mock_template
            
            # Should handle None gracefully
            with pytest.raises(TypeError):
                manager.render_template('test.html', None)

    def test_custom_filter_edge_cases(self):
        """Test custom filters with edge cases"""
        manager = TemplateManager()
        
        # Test truncate_words with empty text
        truncate = manager.env.filters['truncate_words']
        assert truncate("", 10) == ""
        
        # Test truncate_words with very short text
        assert truncate("Hi", 10) == "Hi"
        
        # Test extract_text with nested structure
        extract = manager.env.filters['extract_text']
        nested = {'data': {'text': 'Nested'}}
        assert extract(nested) == ""  # Only checks direct keys

    def test_render_context_empty_build(self):
        """Test building empty context"""
        context = RenderContext()
        result = context.build()
        assert result == {}

    def test_template_cache_thread_safety(self):
        """Test template cache is not shared between instances"""
        manager1 = TemplateManager()
        manager2 = TemplateManager()
        
        manager1._template_cache['test.html'] = Mock()
        assert 'test.html' not in manager2._template_cache