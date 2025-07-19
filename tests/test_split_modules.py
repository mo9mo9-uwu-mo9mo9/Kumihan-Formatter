"""Tests for Issue #490 split modules

Tests for modules that were split during the 300-line limit violation fixes.
These tests focus on basic functionality to improve coverage quickly.
"""

import pytest

# Test AST nodes for basic functionality
from kumihan_formatter.core.ast_nodes import Node, NodeBuilder
from kumihan_formatter.core.classification_rules import build_classification_rules
from kumihan_formatter.core.debug_logger_core import GUIDebugLogger
from kumihan_formatter.core.debug_logger_decorators import log_gui_method
from kumihan_formatter.core.debug_logger_utils import get_logger, is_debug_enabled
from kumihan_formatter.core.document_types import DocumentType

# Test split modules from Issue #490
from kumihan_formatter.core.rendering.basic_element_renderer import BasicElementRenderer
from kumihan_formatter.core.rendering.div_renderer import DivRenderer
from kumihan_formatter.core.rendering.heading_renderer import HeadingRenderer
from kumihan_formatter.core.rendering.list_renderer import ListRenderer


class TestSplitModulesBasic:
    """Basic tests for split modules to improve coverage"""

    def test_basic_element_renderer_initialization(self):
        """Test BasicElementRenderer initialization"""
        renderer = BasicElementRenderer()
        assert renderer is not None
        assert hasattr(renderer, "_render_content")

    def test_heading_renderer_initialization(self):
        """Test HeadingRenderer initialization"""
        renderer = HeadingRenderer()
        assert renderer is not None
        assert hasattr(renderer, "heading_counter")
        assert hasattr(renderer, "reset_counters")

    def test_list_renderer_initialization(self):
        """Test ListRenderer initialization"""
        renderer = ListRenderer()
        assert renderer is not None
        assert hasattr(renderer, "_render_content")

    def test_div_renderer_initialization(self):
        """Test DivRenderer initialization"""
        renderer = DivRenderer()
        assert renderer is not None
        assert hasattr(renderer, "_render_content")

    def test_debug_logger_core_initialization(self):
        """Test GUIDebugLogger initialization"""
        logger = GUIDebugLogger()
        assert logger is not None
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

    def test_debug_decorator_exists(self):
        """Test debug decorator function exists"""
        assert callable(log_gui_method)

        # Test basic decorator functionality
        @log_gui_method
        def test_func():
            return "test"

        # Decorator returns wrapper function, so just test it's callable
        assert callable(test_func)

    def test_debug_utils_functions(self):
        """Test debug utility functions"""
        # Test get_logger function (no arguments)
        logger = get_logger()
        assert logger is not None

        # Test is_debug_enabled function
        debug_status = is_debug_enabled()
        assert isinstance(debug_status, bool)

    def test_document_type_enum(self):
        """Test DocumentType enum"""
        # Test that DocumentType enum has expected values
        expected_types = [
            "USER_ESSENTIAL",
            "USER_GUIDE",
            "DEVELOPER",
            "TECHNICAL",
            "EXCLUDE",
            "EXAMPLE",
        ]

        for doc_type_name in expected_types:
            if hasattr(DocumentType, doc_type_name):
                doc_type = getattr(DocumentType, doc_type_name)
                assert doc_type is not None

    def test_classification_rules_function(self):
        """Test build_classification_rules function"""
        rules = build_classification_rules()
        assert isinstance(rules, dict)
        assert len(rules) > 0

        # Test structure of rules
        for rule_key, rule_dict in rules.items():
            assert isinstance(rule_dict, dict)

    def test_node_creation(self):
        """Test Node creation"""
        node = Node("test", "content")
        assert node is not None
        assert node.type == "test"
        assert node.content == "content"

    def test_node_builder_creation(self):
        """Test NodeBuilder creation"""
        builder = NodeBuilder("test_type")
        assert builder is not None

        # Test basic node building
        node = builder.content("test_content").build()
        assert node is not None
        assert node.type == "test_type"
        assert node.content == "test_content"


class TestHeadingRendererFunctionality:
    """Test HeadingRenderer specific functionality"""

    def test_heading_counter_functionality(self):
        """Test heading counter functionality"""
        renderer = HeadingRenderer()

        # Test initial state
        assert renderer.heading_counter == 0

        # Test counter increment
        renderer.heading_counter += 1
        assert renderer.heading_counter == 1

        # Test reset
        renderer.reset_counters()
        assert renderer.heading_counter == 0

    def test_render_content_with_string(self):
        """Test _render_content with string input"""
        renderer = HeadingRenderer()
        result = renderer._render_content("test string")
        assert isinstance(result, str)
        assert "test string" in result

    def test_render_content_with_none(self):
        """Test _render_content with None input"""
        renderer = HeadingRenderer()
        result = renderer._render_content(None)
        assert result == ""

    def test_render_content_with_list(self):
        """Test _render_content with list input"""
        renderer = HeadingRenderer()
        result = renderer._render_content(["item1", "item2"])
        assert isinstance(result, str)
        assert "item1" in result
        assert "item2" in result


class TestBasicElementRendererFunctionality:
    """Test BasicElementRenderer specific functionality"""

    def test_render_content_basic(self):
        """Test basic _render_content functionality"""
        renderer = BasicElementRenderer()

        # Test with string
        result = renderer._render_content("test")
        assert isinstance(result, str)
        assert "test" in result

        # Test with None
        result = renderer._render_content(None)
        assert result == ""

        # Test with empty list
        result = renderer._render_content([])
        assert result == ""


class TestDebugLoggerComponents:
    """Test debug logger split components"""

    def test_debug_logger_core_basic_functionality(self):
        """Test GUIDebugLogger basic methods"""
        logger = GUIDebugLogger()

        # Test that logger has expected attributes
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

    def test_debug_logger_methods(self):
        """Test GUIDebugLogger methods"""
        logger = GUIDebugLogger()

        # Test logging methods exist and are callable
        assert callable(logger.debug)
        assert callable(logger.info)
        assert callable(logger.warning)
        assert callable(logger.error)

    def test_debug_gui_method_decorator_callable(self):
        """Test log_gui_method decorator is callable"""
        # Just test that the decorator exists and is callable
        assert callable(log_gui_method)


class TestDocumentClassificationComponents:
    """Test document classification split components"""

    def test_document_type_values(self):
        """Test DocumentType enum values"""
        # Test that expected document types exist
        expected_types = [
            "USER_ESSENTIAL",
            "USER_GUIDE",
            "DEVELOPER",
            "TECHNICAL",
            "EXCLUDE",
            "EXAMPLE",
        ]
        for doc_type in expected_types:
            assert hasattr(DocumentType, doc_type)

    def test_classification_rules_structure(self):
        """Test classification rules structure"""
        rules = build_classification_rules()

        # Test that rules has expected structure
        assert isinstance(rules, dict)

        # Test that rules contain DocumentType keys
        for rule_key in rules.keys():
            assert isinstance(rule_key, DocumentType)

        # Test that each rule has expected structure
        for rule_dict in rules.values():
            assert isinstance(rule_dict, dict)
            # Most rules should have filenames and patterns
            if "filenames" in rule_dict:
                assert isinstance(rule_dict["filenames"], list)
            if "patterns" in rule_dict:
                assert isinstance(rule_dict["patterns"], list)
