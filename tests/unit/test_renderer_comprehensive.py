"""
Renderer modules comprehensive test coverage.

Tests rendering functionality to achieve 80% coverage goal.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile

# Import only existing modules
from kumihan_formatter.core.ast_nodes.node import Node

try:
    from kumihan_formatter.core.rendering.html_renderer import HTMLRenderer
except ImportError:
    HTMLRenderer = None

try:
    from kumihan_formatter.core.rendering.renderer_base import RendererBase
except ImportError:
    RendererBase = None

try:
    from kumihan_formatter.core.rendering.style_manager import StyleManager
except ImportError:
    StyleManager = None

try:
    from kumihan_formatter.core.rendering.template_engine import TemplateEngine
except ImportError:
    TemplateEngine = None


@pytest.mark.unit
@pytest.mark.renderer
@pytest.mark.skipif(HTMLRenderer is None, reason="HTMLRenderer not available")
class TestHTMLRendererCoverage:
    """HTMLRenderer comprehensive coverage tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = HTMLRenderer()
        self.style_manager = StyleManager()

    def test_html_renderer_initialization(self):
        """Test HTMLRenderer initialization."""
        assert self.renderer is not None
        assert hasattr(self.renderer, "render_nodes")
        assert hasattr(self.renderer, "render_node")
        assert hasattr(self.renderer, "render_text")
        assert hasattr(self.renderer, "render_element")

    def test_render_text_node(self):
        """Test rendering text nodes."""
        text_node = Node(type="text", content="Hello World")
        result = self.renderer.render_node(text_node)

        assert result is not None
        assert isinstance(result, str)
        assert "Hello World" in result

    def test_render_element_node(self):
        """Test rendering element nodes."""
        element_node = Node(
            type="element",
            tag="p",
            content="Paragraph content",
            attributes={"class": "test"},
        )
        result = self.renderer.render_node(element_node)

        assert result is not None
        assert isinstance(result, str)
        assert "<p" in result
        assert 'class="test"' in result
        assert "Paragraph content" in result

    def test_render_bold_node(self):
        """Test rendering bold nodes."""
        bold_node = Node(type="element", tag="strong", content="Bold text")
        result = self.renderer.render_node(bold_node)

        assert result is not None
        assert "<strong>" in result
        assert "Bold text" in result
        assert "</strong>" in result

    def test_render_heading_nodes(self):
        """Test rendering heading nodes."""
        for level in range(1, 6):
            heading_node = Node(
                type="element", tag=f"h{level}", content=f"Heading {level}"
            )
            result = self.renderer.render_node(heading_node)

            assert result is not None
            assert f"<h{level}" in result
            assert f"Heading {level}" in result
            assert f"</h{level}>" in result

    def test_render_list_nodes(self):
        """Test rendering list nodes."""
        # Unordered list
        ul_node = Node(
            type="element",
            tag="ul",
            children=[
                Node(type="element", tag="li", content="Item 1"),
                Node(type="element", tag="li", content="Item 2"),
            ],
        )
        result = self.renderer.render_node(ul_node)

        assert result is not None
        assert "<ul>" in result
        assert "<li>Item 1</li>" in result
        assert "<li>Item 2</li>" in result
        assert "</ul>" in result

    def test_render_nested_nodes(self):
        """Test rendering nested node structures."""
        nested_node = Node(
            type="element",
            tag="div",
            children=[
                Node(type="element", tag="p", content="First paragraph"),
                Node(
                    type="element",
                    tag="div",
                    children=[Node(type="text", content="Nested content")],
                ),
            ],
        )
        result = self.renderer.render_node(nested_node)

        assert result is not None
        assert "<div>" in result
        assert "<p>First paragraph</p>" in result
        assert "Nested content" in result

    def test_render_with_attributes(self):
        """Test rendering nodes with various attributes."""
        # Class attribute
        node_with_class = Node(
            type="element",
            tag="div",
            content="Content",
            attributes={"class": "my-class"},
        )
        result = self.renderer.render_node(node_with_class)
        assert 'class="my-class"' in result

        # Multiple attributes
        node_with_attrs = Node(
            type="element",
            tag="div",
            content="Content",
            attributes={"id": "test-id", "class": "test-class", "data-value": "123"},
        )
        result = self.renderer.render_node(node_with_attrs)
        assert 'id="test-id"' in result
        assert 'class="test-class"' in result
        assert 'data-value="123"' in result

    def test_render_special_characters(self):
        """Test rendering with special HTML characters."""
        special_node = Node(
            type="text", content='<script>alert("test")</script> & "quotes"'
        )
        result = self.renderer.render_node(special_node)

        # Should escape HTML entities
        assert result is not None
        assert "&lt;" in result or "<script>" not in result
        assert "&amp;" in result or "&" not in result or result.count("&") == 1

    def test_render_empty_content(self):
        """Test rendering nodes with empty content."""
        empty_node = Node(type="text", content="")
        result = self.renderer.render_node(empty_node)

        assert result is not None
        assert isinstance(result, str)

    def test_render_nodes_collection(self):
        """Test rendering collection of nodes."""
        nodes = [
            Node(type="text", content="First"),
            Node(type="element", tag="strong", content="Bold"),
            Node(type="text", content="Last"),
        ]
        result = self.renderer.render_nodes(nodes)

        assert result is not None
        assert "First" in result
        assert "<strong>Bold</strong>" in result
        assert "Last" in result


@pytest.mark.unit
@pytest.mark.renderer
@pytest.mark.skipif(StyleManager is None, reason="StyleManager not available")
class TestStyleManagerCoverage:
    """StyleManager comprehensive coverage tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.style_manager = StyleManager()

    def test_style_manager_initialization(self):
        """Test StyleManager initialization."""
        assert self.style_manager is not None
        assert hasattr(self.style_manager, "add_style")
        assert hasattr(self.style_manager, "get_styles")
        assert hasattr(self.style_manager, "generate_css")

    def test_add_style_rules(self):
        """Test adding style rules."""
        self.style_manager.add_style(".test", {"color": "red", "font-size": "14px"})
        styles = self.style_manager.get_styles()

        assert ".test" in styles
        assert styles[".test"]["color"] == "red"
        assert styles[".test"]["font-size"] == "14px"

    def test_add_multiple_styles(self):
        """Test adding multiple style rules."""
        styles_to_add = {
            ".header": {"font-size": "24px", "font-weight": "bold"},
            ".content": {"margin": "10px", "padding": "5px"},
            "#footer": {"text-align": "center"},
        }

        for selector, properties in styles_to_add.items():
            self.style_manager.add_style(selector, properties)

        all_styles = self.style_manager.get_styles()
        for selector in styles_to_add:
            assert selector in all_styles

    def test_generate_css_output(self):
        """Test CSS generation."""
        self.style_manager.add_style(".test", {"color": "blue"})
        self.style_manager.add_style("p", {"margin": "0"})

        css = self.style_manager.generate_css()

        assert isinstance(css, str)
        assert ".test" in css
        assert "color: blue" in css
        assert "p" in css
        assert "margin: 0" in css

    def test_override_existing_styles(self):
        """Test overriding existing styles."""
        # Add initial style
        self.style_manager.add_style(".test", {"color": "red"})

        # Override with new style
        self.style_manager.add_style(".test", {"color": "blue", "font-size": "16px"})

        styles = self.style_manager.get_styles()
        assert styles[".test"]["color"] == "blue"
        assert styles[".test"]["font-size"] == "16px"

    def test_merge_styles(self):
        """Test merging styles."""
        # Add base style
        self.style_manager.add_style(".test", {"color": "red"})

        # Merge additional properties
        self.style_manager.merge_style(".test", {"font-size": "16px"})

        styles = self.style_manager.get_styles()
        assert styles[".test"]["color"] == "red"
        assert styles[".test"]["font-size"] == "16px"

    def test_remove_styles(self):
        """Test removing styles."""
        self.style_manager.add_style(".test", {"color": "red"})
        assert ".test" in self.style_manager.get_styles()

        self.style_manager.remove_style(".test")
        assert ".test" not in self.style_manager.get_styles()

    def test_clear_all_styles(self):
        """Test clearing all styles."""
        self.style_manager.add_style(".test1", {"color": "red"})
        self.style_manager.add_style(".test2", {"color": "blue"})

        self.style_manager.clear_styles()
        styles = self.style_manager.get_styles()
        assert len(styles) == 0


@pytest.mark.unit
@pytest.mark.renderer
@pytest.mark.skipif(TemplateEngine is None, reason="TemplateEngine not available")
class TestTemplateEngineCoverage:
    """TemplateEngine comprehensive coverage tests."""

    def setup_method(self):
        """Set up test fixtures."""
        self.template_engine = TemplateEngine()

    def test_template_engine_initialization(self):
        """Test TemplateEngine initialization."""
        assert self.template_engine is not None
        assert hasattr(self.template_engine, "render_template")
        assert hasattr(self.template_engine, "load_template")
        assert hasattr(self.template_engine, "set_template_dir")

    def test_simple_template_rendering(self):
        """Test simple template rendering."""
        template = "Hello, {{name}}!"
        context = {"name": "World"}

        result = self.template_engine.render_template(template, context)

        assert result is not None
        assert "Hello, World!" in result

    def test_html_template_rendering(self):
        """Test HTML template rendering."""
        template = """
        <html>
        <head><title>{{title}}</title></head>
        <body>
            <h1>{{heading}}</h1>
            <div>{{content}}</div>
        </body>
        </html>
        """
        context = {
            "title": "Test Page",
            "heading": "Welcome",
            "content": "This is test content",
        }

        result = self.template_engine.render_template(template, context)

        assert result is not None
        assert "Test Page" in result
        assert "Welcome" in result
        assert "This is test content" in result

    def test_template_with_loops(self):
        """Test template with loop constructs."""
        template = """
        <ul>
        {% for item in items %}
            <li>{{item}}</li>
        {% endfor %}
        </ul>
        """
        context = {"items": ["Item 1", "Item 2", "Item 3"]}

        result = self.template_engine.render_template(template, context)

        assert result is not None
        assert "<ul>" in result
        assert "<li>Item 1</li>" in result
        assert "<li>Item 2</li>" in result
        assert "<li>Item 3</li>" in result

    def test_template_with_conditionals(self):
        """Test template with conditional constructs."""
        template = """
        {% if show_header %}
            <h1>{{title}}</h1>
        {% endif %}
        <p>Content here</p>
        """

        # Test with condition true
        context = {"show_header": True, "title": "My Title"}
        result = self.template_engine.render_template(template, context)
        assert "<h1>My Title</h1>" in result

        # Test with condition false
        context = {"show_header": False, "title": "My Title"}
        result = self.template_engine.render_template(template, context)
        assert "<h1>My Title</h1>" not in result

    def test_load_template_from_file(self):
        """Test loading template from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as tf:
            tf.write("<html><head><title>{{title}}</title></head></html>")
            tf.flush()

            try:
                template_content = self.template_engine.load_template(tf.name)
                assert template_content is not None
                assert "{{title}}" in template_content
            finally:
                Path(tf.name).unlink(missing_ok=True)

    def test_template_error_handling(self):
        """Test template error handling."""
        # Invalid template syntax
        invalid_template = "Hello {{name"  # Missing closing braces
        context = {"name": "World"}

        # Should handle gracefully
        try:
            result = self.template_engine.render_template(invalid_template, context)
            assert result is not None
        except Exception as e:
            # Should raise appropriate template error
            assert isinstance(e, (ValueError, TypeError, RuntimeError))

    def test_missing_context_variables(self):
        """Test handling missing context variables."""
        template = "Hello, {{missing_var}}!"
        context = {}

        # Should handle missing variables gracefully
        result = self.template_engine.render_template(template, context)
        assert result is not None


@pytest.mark.unit
@pytest.mark.renderer
@pytest.mark.skipif(RendererBase is None, reason="RendererBase not available")
class TestRendererBaseCoverage:
    """RendererBase coverage tests."""

    def test_renderer_base_interface(self):
        """Test RendererBase interface."""

        # Create mock renderer extending base
        class MockRenderer(RendererBase):
            def render_node(self, node):
                return f"<mock>{node.content}</mock>"

        renderer = MockRenderer()

        # Test basic interface
        assert hasattr(renderer, "render_node")
        assert hasattr(renderer, "render_nodes")

        # Test node rendering
        test_node = Node(type="text", content="test")
        result = renderer.render_node(test_node)
        assert "<mock>test</mock>" in result

    def test_renderer_configuration(self):
        """Test renderer configuration."""

        class ConfigurableRenderer(RendererBase):
            def __init__(self, config=None):
                super().__init__(config)
                self.config = config or {}

            def render_node(self, node):
                return f"<{self.config.get('tag', 'div')}>{node.content}</{self.config.get('tag', 'div')}>"

        config = {"tag": "span"}
        renderer = ConfigurableRenderer(config)

        test_node = Node(type="text", content="configured")
        result = renderer.render_node(test_node)
        assert "<span>configured</span>" in result
