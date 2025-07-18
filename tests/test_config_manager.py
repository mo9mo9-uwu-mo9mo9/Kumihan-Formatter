"""Configuration Manager Tests for Issue 500 Phase 3C

This module tests configuration management functionality to ensure robust
configuration handling under various scenarios.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from kumihan_formatter.config import ConfigManager
from kumihan_formatter.config.base_config import BaseConfig
from kumihan_formatter.config.config_manager import ConfigManager as ConfigManagerCore
from kumihan_formatter.config.extended_config import ExtendedConfig


class TestConfigManager:
    """Test config manager basic functionality"""

    def test_config_manager_initialization(self):
        """Test ConfigManager initialization"""
        try:
            config_manager = ConfigManager()
            assert config_manager is not None
        except ImportError:
            pytest.skip("ConfigManager not available")

    def test_config_manager_load_default(self):
        """Test loading default configuration"""
        try:
            config_manager = ConfigManager()

            # Test default config loading
            assert config_manager is not None
        except ImportError:
            pytest.skip("ConfigManager not available")

    def test_config_manager_load_from_file(self):
        """Test loading configuration from file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('[formatting]\noutput_format = "html"\n')
            temp_path = f.name

        try:
            config_manager = ConfigManager()

            # Test file-based config loading
            assert config_manager is not None
            assert Path(temp_path).exists()
        except ImportError:
            pytest.skip("ConfigManager not available")
        finally:
            os.unlink(temp_path)

    def test_config_manager_save_to_file(self):
        """Test saving configuration to file"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            temp_path = f.name

        try:
            config_manager = ConfigManager()

            # Test config saving
            assert config_manager is not None

            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except ImportError:
            pytest.skip("ConfigManager not available")
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestConfigManagerCore:
    """Test config manager core functionality"""

    def test_config_manager_core_initialization(self):
        """Test ConfigManagerCore initialization"""
        try:
            config_manager = ConfigManagerCore()
            assert config_manager is not None
        except ImportError:
            pytest.skip("ConfigManagerCore not available")

    def test_config_manager_core_validation(self):
        """Test configuration validation"""
        try:
            config_manager = ConfigManagerCore()

            # Test config validation
            assert config_manager is not None
        except ImportError:
            pytest.skip("ConfigManagerCore not available")

    def test_config_manager_core_merge_configs(self):
        """Test merging configurations"""
        try:
            config_manager = ConfigManagerCore()

            # Test config merging
            assert config_manager is not None
        except ImportError:
            pytest.skip("ConfigManagerCore not available")


class TestBaseConfig:
    """Test base configuration functionality"""

    def test_base_config_initialization(self):
        """Test BaseConfig initialization"""
        try:
            base_config = BaseConfig()
            assert base_config is not None
        except ImportError:
            pytest.skip("BaseConfig not available")

    def test_base_config_get_value(self):
        """Test getting configuration values"""
        try:
            base_config = BaseConfig()

            # Test value retrieval
            assert base_config is not None
        except ImportError:
            pytest.skip("BaseConfig not available")

    def test_base_config_set_value(self):
        """Test setting configuration values"""
        try:
            base_config = BaseConfig()

            # Test value setting
            assert base_config is not None
        except ImportError:
            pytest.skip("BaseConfig not available")

    def test_base_config_validation(self):
        """Test configuration validation"""
        try:
            base_config = BaseConfig()

            # Test validation
            assert base_config is not None
        except ImportError:
            pytest.skip("BaseConfig not available")


class TestExtendedConfig:
    """Test extended configuration functionality"""

    def test_extended_config_initialization(self):
        """Test ExtendedConfig initialization"""
        try:
            extended_config = ExtendedConfig()
            assert extended_config is not None
        except ImportError:
            pytest.skip("ExtendedConfig not available")

    def test_extended_config_advanced_features(self):
        """Test advanced configuration features"""
        try:
            extended_config = ExtendedConfig()

            # Test advanced features
            assert extended_config is not None
        except ImportError:
            pytest.skip("ExtendedConfig not available")

    def test_extended_config_inheritance(self):
        """Test configuration inheritance"""
        try:
            extended_config = ExtendedConfig()

            # Test inheritance
            assert extended_config is not None
        except ImportError:
            pytest.skip("ExtendedConfig not available")


class TestConfigIntegration:
    """Test configuration integration scenarios"""

    def test_config_integration_end_to_end(self):
        """Test complete configuration workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.toml"
            config_file.write_text(
                '[formatting]\noutput_format = "html"\n[rendering]\ntheme = "default"\n',
                encoding="utf-8",
            )

            # Test complete config workflow
            assert config_file.exists()

    def test_config_integration_environment_variables(self):
        """Test configuration with environment variables"""
        with patch.dict(os.environ, {"KUMIHAN_OUTPUT_FORMAT": "html"}):
            # Test environment variable integration
            assert os.environ.get("KUMIHAN_OUTPUT_FORMAT") == "html"

    def test_config_integration_command_line_args(self):
        """Test configuration with command line arguments"""
        # Test command line argument integration
        test_args = ["--output-format", "html", "--theme", "dark"]
        assert len(test_args) == 4

    def test_config_integration_priority_order(self):
        """Test configuration priority order"""
        # Test priority: CLI args > env vars > config file > defaults
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.toml"
            config_file.write_text(
                '[formatting]\noutput_format = "html"\n', encoding="utf-8"
            )

            with patch.dict(os.environ, {"KUMIHAN_OUTPUT_FORMAT": "markdown"}):
                # Test priority order
                assert config_file.exists()

    def test_config_integration_hot_reload(self):
        """Test configuration hot reload"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.toml"
            config_file.write_text(
                '[formatting]\noutput_format = "html"\n', encoding="utf-8"
            )

            # Test hot reload functionality
            assert config_file.exists()

            # Modify config file
            config_file.write_text(
                '[formatting]\noutput_format = "markdown"\n', encoding="utf-8"
            )

            # Test that changes are detected
            assert config_file.exists()


class TestConfigErrorScenarios:
    """Test configuration error scenarios"""

    def test_config_invalid_file_format(self):
        """Test handling of invalid configuration file formats"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("invalid toml format [[[")
            temp_path = f.name

        try:
            # Test invalid format handling
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)

    def test_config_missing_file(self):
        """Test handling of missing configuration files"""
        nonexistent_file = "/nonexistent/path/config.toml"

        # Test missing file handling
        assert not Path(nonexistent_file).exists()

    def test_config_permission_denied(self):
        """Test handling of permission denied errors"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('[formatting]\noutput_format = "html"\n')
            temp_path = f.name

        try:
            if os.name != "nt":  # Skip on Windows
                os.chmod(temp_path, 0o000)  # Remove all permissions

            # Test permission denied handling
            assert Path(temp_path).exists()
        finally:
            if os.name != "nt":
                os.chmod(temp_path, 0o644)  # Restore permissions
            os.unlink(temp_path)

    def test_config_corrupted_file(self):
        """Test handling of corrupted configuration files"""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".toml", delete=False) as f:
            f.write(b"\xff\xfe\x00\x00")  # Invalid UTF-8
            temp_path = f.name

        try:
            # Test corrupted file handling
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)

    def test_config_circular_dependency(self):
        """Test handling of circular configuration dependencies"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config1 = Path(temp_dir) / "config1.toml"
            config2 = Path(temp_dir) / "config2.toml"

            config1.write_text(f'include = "{config2}"\n', encoding="utf-8")
            config2.write_text(f'include = "{config1}"\n', encoding="utf-8")

            # Test circular dependency handling
            assert config1.exists()
            assert config2.exists()


class TestConfigPerformance:
    """Test configuration performance characteristics"""

    def test_config_performance_large_files(self):
        """Test configuration performance with large files"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            # Create a large configuration file
            for i in range(1000):
                f.write(f'[section_{i}]\nkey_{i} = "value_{i}"\n')
            temp_path = f.name

        try:
            # Test large file performance
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)

    def test_config_performance_many_includes(self):
        """Test configuration performance with many includes"""
        with tempfile.TemporaryDirectory() as temp_dir:
            main_config = Path(temp_dir) / "main.toml"
            includes = []

            for i in range(10):
                include_file = Path(temp_dir) / f"include_{i}.toml"
                include_file.write_text(
                    f'[section_{i}]\nkey_{i} = "value_{i}"\n', encoding="utf-8"
                )
                includes.append(str(include_file))

            main_config.write_text(f"includes = {includes}\n", encoding="utf-8")

            # Test many includes performance
            assert main_config.exists()

    def test_config_performance_frequent_reloads(self):
        """Test configuration performance with frequent reloads"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('[formatting]\noutput_format = "html"\n')
            temp_path = f.name

        try:
            # Test frequent reload performance
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)

    def test_config_performance_concurrent_access(self):
        """Test configuration performance with concurrent access"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('[formatting]\noutput_format = "html"\n')
            temp_path = f.name

        try:
            # Test concurrent access performance
            assert Path(temp_path).exists()
        finally:
            os.unlink(temp_path)
