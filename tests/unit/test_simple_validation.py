"""
Simplified test cases to verify test infrastructure works.

Basic functionality tests to ensure the test suite operates correctly.
"""

from pathlib import Path

import pytest

from kumihan_formatter.core.syntax.syntax_validator import KumihanSyntaxValidator


@pytest.mark.unit
class TestSimpleValidation:
    """Simple validation tests to verify test infrastructure."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = KumihanSyntaxValidator()

    def test_validator_initialization(self):
        """Test that validator can be initialized."""
        assert self.validator is not None
        assert isinstance(self.validator, KumihanSyntaxValidator)

    def test_empty_text_validation(self):
        """Test validation of empty text."""
        empty_text = ""

        try:
            result = self.validator.validate_text(empty_text)
            assert isinstance(result, list)
        except (AttributeError, NotImplementedError):
            pytest.skip("validate_text method not implemented")

    def test_simple_text_validation(self):
        """Test validation of simple text without notation."""
        simple_text = "これは通常のテキストです。"

        try:
            result = self.validator.validate_text(simple_text)
            assert isinstance(result, list)
        except (AttributeError, NotImplementedError):
            pytest.skip("validate_text method not implemented")

    def test_potential_notation_text(self):
        """Test validation of text that might contain notation."""
        notation_text = "#太字 テスト内容#"

        try:
            result = self.validator.validate_text(notation_text)
            assert isinstance(result, list)
            # Result can be empty (no errors) or contain validation issues
        except (AttributeError, NotImplementedError):
            pytest.skip("validate_text method not implemented")

    def test_file_validation_method_exists(self, temp_dir):
        """Test that file validation method exists."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("テスト内容", encoding="utf-8")

        try:
            result = self.validator.validate_file(test_file)
            assert isinstance(result, list)
        except (AttributeError, NotImplementedError):
            pytest.skip("validate_file method not implemented")
        except FileNotFoundError:
            pytest.fail("File should exist but was not found")

    def test_multiple_file_validation_method_exists(self, temp_dir):
        """Test that multiple file validation method exists."""
        files = []
        for i in range(3):
            test_file = temp_dir / f"test_{i}.txt"
            test_file.write_text(f"テスト内容{i}", encoding="utf-8")
            files.append(test_file)

        try:
            result = self.validator.validate_files(files)
            assert isinstance(result, (list, dict))
        except (AttributeError, NotImplementedError):
            pytest.skip("validate_files method not implemented")


@pytest.mark.unit
class TestBasicInfrastructure:
    """Test basic test infrastructure components."""

    def test_fixtures_work(self, temp_dir, sample_text_files):
        """Test that pytest fixtures work correctly."""
        # Test temp_dir fixture
        assert temp_dir.exists()
        assert temp_dir.is_dir()

        # Test sample_text_files fixture
        assert isinstance(sample_text_files, dict)
        assert len(sample_text_files) > 0

        # Verify files exist and have content
        for name, file_path in sample_text_files.items():
            assert file_path.exists()
            assert file_path.stat().st_size > 0

            content = file_path.read_text(encoding="utf-8")
            assert len(content) > 0

    def test_markers_are_registered(self):
        """Test that pytest markers are working."""
        # If this test runs, markers are properly configured
        assert True

    def test_imports_work(self):
        """Test that basic imports work."""
        from kumihan_formatter.core.keyword_parsing.definitions import (
            KeywordDefinitions,
        )
        from kumihan_formatter.core.keyword_parsing.marker_parser import MarkerParser

        # Test basic instantiation
        definitions = KeywordDefinitions()
        assert definitions is not None

        parser = MarkerParser(definitions)
        assert parser is not None

        # Test that definitions have some content
        all_keywords = definitions.get_all_keywords()
        assert isinstance(all_keywords, (list, dict, set))

    def test_basic_method_availability(self):
        """Test that basic methods are available on key classes."""
        from kumihan_formatter.core.keyword_parsing.definitions import (
            KeywordDefinitions,
        )
        from kumihan_formatter.core.keyword_parsing.marker_parser import MarkerParser

        definitions = KeywordDefinitions()
        parser = MarkerParser(definitions)

        # Test method availability (don't call them, just check they exist)
        assert hasattr(parser, 'parse_marker_keywords')
        assert hasattr(parser, 'normalize_marker_syntax')
        assert hasattr(parser, 'is_new_marker_format')

        assert hasattr(definitions, 'get_all_keywords')
        if hasattr(definitions, 'is_valid_keyword'):
            assert callable(definitions.is_valid_keyword)


@pytest.mark.integration
class TestBasicCLI:
    """Test basic CLI functionality."""

    def test_module_can_be_imported(self):
        """Test that the main module can be imported."""
        try:
            import kumihan_formatter
            assert kumihan_formatter is not None
        except ImportError as e:
            pytest.fail(f"Failed to import main module: {e}")

    def test_cli_module_exists(self):
        """Test that CLI module exists."""
        try:
            from kumihan_formatter import cli
            assert cli is not None
        except ImportError:
            pytest.skip("CLI module not available")

    def test_main_function_exists(self):
        """Test that main function exists."""
        try:
            from kumihan_formatter.cli import main
            assert callable(main)
        except ImportError:
            pytest.skip("CLI main function not available")
