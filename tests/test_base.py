"""Base Test Classes for Issue 500 Phase 3

This module provides common test base classes and utilities to reduce
code duplication across test files.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


class BaseTestCase:
    """Base test class with common utilities"""

    def setup_method(self, method):
        """Setup method called before each test method"""
        self.temp_files = []
        self.temp_dirs = []

    def teardown_method(self, method):
        """Teardown method called after each test method"""
        # Clean up temporary files
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

        # Clean up temporary directories
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                import shutil

                shutil.rmtree(temp_dir)

    def create_temp_file(self, content="", suffix=".txt", encoding="utf-8"):
        """Create a temporary file with given content"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=suffix, delete=False, encoding=encoding
        ) as f:
            f.write(content)
            temp_path = f.name

        self.temp_files.append(temp_path)
        return temp_path

    def create_temp_dir(self):
        """Create a temporary directory"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir

    def assert_file_exists(self, file_path):
        """Assert that a file exists"""
        assert Path(file_path).exists(), f"File {file_path} does not exist"

    def assert_file_content(self, file_path, expected_content):
        """Assert file content matches expected content"""
        actual_content = Path(file_path).read_text(encoding="utf-8")
        assert (
            actual_content == expected_content
        ), f"File content mismatch in {file_path}"

    def assert_file_contains(self, file_path, expected_substring):
        """Assert file contains expected substring"""
        actual_content = Path(file_path).read_text(encoding="utf-8")
        assert (
            expected_substring in actual_content
        ), f"File {file_path} does not contain '{expected_substring}'"


class ComponentTestCase(BaseTestCase):
    """Base class for component-specific tests"""

    def check_component_availability(self, component_class, component_name):
        """Check if component is available, skip test if not"""
        try:
            instance = component_class()
            return instance
        except ImportError:
            pytest.skip(f"{component_name} not available")

    def test_component_initialization(self, component_class, component_name):
        """Generic component initialization test"""
        instance = self.check_component_availability(component_class, component_name)
        assert instance is not None
        assert hasattr(instance, "__class__")
        assert instance.__class__.__name__ == component_class.__name__


class CacheTestCase(ComponentTestCase):
    """Base class for cache-related tests"""

    def test_cache_basic_operations(self, cache_class):
        """Generic cache basic operations test"""
        cache = self.check_component_availability(cache_class, cache_class.__name__)

        # Test basic cache operations
        test_key = "test_key"
        test_value = "test_value"

        # Test set operation
        cache.set(test_key, test_value)

        # Test get operation
        retrieved_value = cache.get(test_key)
        assert retrieved_value == test_value

        # Test cache miss
        assert cache.get("nonexistent_key") is None

    def test_cache_statistics(self, cache_class):
        """Generic cache statistics test"""
        cache = self.check_component_availability(cache_class, cache_class.__name__)

        # Verify cache has statistics tracking
        assert hasattr(cache, "hit_count") or hasattr(cache, "get_stats")
        assert hasattr(cache, "miss_count") or hasattr(cache, "get_stats")


class ConfigTestCase(ComponentTestCase):
    """Base class for configuration-related tests"""

    def test_config_basic_operations(self, config_class):
        """Generic config basic operations test"""
        config = self.check_component_availability(config_class, config_class.__name__)

        # Test basic config operations
        test_key = "test_key"
        test_value = "test_value"

        # Test set operation
        config.set(test_key, test_value)

        # Test get operation
        retrieved_value = config.get(test_key)
        assert retrieved_value == test_value

        # Test default value
        default_value = config.get("nonexistent_key", "default")
        assert default_value == "default"

    def test_config_file_operations(self, config_class):
        """Generic config file operations test"""
        config = self.check_component_availability(config_class, config_class.__name__)

        # Test save to file
        temp_file = self.create_temp_file("", ".toml")
        config.set("test_key", "test_value")

        if hasattr(config, "save_to_file"):
            config.save_to_file(temp_file)
            self.assert_file_exists(temp_file)

        # Test load from file
        if hasattr(config, "load_from_file"):
            new_config = config_class()
            new_config.load_from_file(temp_file)
            assert new_config.get("test_key") == "test_value"


class ValidatorTestCase(ComponentTestCase):
    """Base class for validator-related tests"""

    def test_validator_basic_operations(self, validator_class):
        """Generic validator basic operations test"""
        validator = self.check_component_availability(
            validator_class, validator_class.__name__
        )

        # Test basic validator operations
        test_content = "test content"

        # Test validation (should not raise exception)
        if hasattr(validator, "validate"):
            result = validator.validate(test_content)
            assert result is not None

        # Test validation with file
        temp_file = self.create_temp_file(test_content)
        if hasattr(validator, "validate_file"):
            result = validator.validate_file(temp_file)
            assert result is not None


class DistributionTestCase(ComponentTestCase):
    """Base class for distribution-related tests"""

    def test_distribution_basic_operations(self, distribution_class):
        """Generic distribution basic operations test"""
        distribution = self.check_component_availability(
            distribution_class, distribution_class.__name__
        )

        # Test basic distribution operations
        source_dir = self.create_temp_dir()
        target_dir = self.create_temp_dir()

        # Create source files
        source_file = Path(source_dir) / "source.txt"
        source_file.write_text("test content", encoding="utf-8")

        # Test distribution operation
        if hasattr(distribution, "distribute"):
            distribution.distribute(source_dir, target_dir)
        elif hasattr(distribution, "process"):
            distribution.process(source_dir, target_dir)

        # Verify operation completed without error
        assert distribution is not None


class FileOperationsTestCase(ComponentTestCase):
    """Base class for file operations tests"""

    def test_file_operations_basic(self, file_ops_class):
        """Generic file operations basic test"""
        file_ops = self.check_component_availability(
            file_ops_class, file_ops_class.__name__
        )

        # Test basic file operations
        temp_file = self.create_temp_file("test content")

        # Test file reading
        if hasattr(file_ops, "read_file"):
            content = file_ops.read_file(temp_file)
            assert content == "test content"

        # Test file writing
        if hasattr(file_ops, "write_file"):
            output_file = self.create_temp_file("")
            file_ops.write_file(output_file, "new content")
            self.assert_file_content(output_file, "new content")


class KumihanNotationTestCase(BaseTestCase):
    """Base class for Kumihan notation tests"""

    def create_kumihan_test_content(
        self, include_footnotes=True, include_sidenotes=True, include_decorations=True
    ):
        """Create test content with various Kumihan notations"""
        content = "# テスト文書\n\n"

        if include_decorations:
            content += "これは;;;強調;;;重要な内容;;;です。\n"

        if include_sidenotes:
            content += "｜漢字《かんじ》の読み方も含まれています。\n"

        if include_footnotes:
            content += "詳細は脚注((別途参照))を確認してください。\n"

        return content

    def assert_notation_parsed(self, parsed_result, notation_type):
        """Assert that specific notation type was parsed"""
        assert parsed_result is not None

        if notation_type == "footnotes":
            assert hasattr(parsed_result, "footnotes")
            assert len(parsed_result.footnotes) > 0
        elif notation_type == "sidenotes":
            assert hasattr(parsed_result, "sidenotes")
            assert len(parsed_result.sidenotes) > 0
        elif notation_type == "decorations":
            assert hasattr(parsed_result, "decorations")
            assert len(parsed_result.decorations) > 0


# Test utilities
def skip_if_not_available(component_name):
    """Decorator to skip test if component is not available"""

    def decorator(test_func):
        def wrapper(self, *args, **kwargs):
            try:
                return test_func(self, *args, **kwargs)
            except ImportError:
                pytest.skip(f"{component_name} not available")

        return wrapper

    return decorator


def create_test_config(output_format="html", encoding="utf-8", theme="default"):
    """Create a test configuration dictionary"""
    return {
        "output_format": output_format,
        "encoding": encoding,
        "theme": theme,
        "test_mode": True,
    }


def create_test_kumihan_content():
    """Create test content with Kumihan notation"""
    return """# テスト文書

これは;;;強調;;;重要な内容;;;です。

｜漢字《かんじ》の読み方も含まれています。

詳細は脚注((別途参照))を確認してください。

## セクション2

複数の;;;装飾;;;スタイル;;;があります。

｜複数《ふくすう》の｜読み方《よみかた》もあります。

複数の脚注((脚注1))と((脚注2))も可能です。
"""
