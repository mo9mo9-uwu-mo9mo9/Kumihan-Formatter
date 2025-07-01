"""Comprehensive tests for config.py module

Tests for Issue #351 - Phase 2 priority B (80%+ coverage target)
"""

import pytest
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, mock_open

from kumihan_formatter.config import Config, load_config


class TestConfigInit:
    """Test Config initialization"""

    def test_init_default(self):
        """Test Config initialization without config path"""
        config = Config()
        assert config.config_path is None
        assert config.config == Config.DEFAULT_CONFIG
        assert config.is_loaded is True

    def test_init_with_valid_config_path(self):
        """Test Config initialization with valid config path"""
        mock_yaml = {"theme": "custom", "css": {"text_color": "#000"}}
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(mock_yaml))):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    config = Config("config.yaml")
                    assert config.config_path == "config.yaml"
                    assert config.config["theme"] == "custom"

    def test_init_with_invalid_config_path(self):
        """Test Config initialization with invalid config path"""
        with patch('pathlib.Path.exists', return_value=False):
            config = Config("nonexistent.yaml")
            assert config.config_path == "nonexistent.yaml"
            assert config.config == Config.DEFAULT_CONFIG
            assert config.is_loaded is True

    def test_init_with_none_path(self):
        """Test Config initialization with None path"""
        config = Config(None)
        assert config.config_path is None
        assert config.config == Config.DEFAULT_CONFIG


class TestLoadConfig:
    """Test load_config method"""

    def test_load_yaml_config(self):
        """Test loading YAML config file"""
        config = Config()
        mock_yaml = {"theme": "dark", "css": {"background_color": "#000"}}
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(mock_yaml))):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    result = config.load_config("test.yaml")
                    assert result is True
                    assert config.config["theme"] == "dark"

    def test_load_yml_config(self):
        """Test loading YML config file"""
        config = Config()
        mock_yaml = {"theme": "light"}
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(mock_yaml))):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    result = config.load_config("test.yml")
                    assert result is True
                    assert config.config["theme"] == "light"

    def test_load_json_config(self):
        """Test loading JSON config file"""
        config = Config()
        mock_json = {"theme": "custom", "font_family": "Arial"}
        
        with patch('builtins.open', mock_open(read_data=json.dumps(mock_json))):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    result = config.load_config("test.json")
                    assert result is True
                    assert config.config["theme"] == "custom"
                    assert config.config["font_family"] == "Arial"

    def test_load_nonexistent_file(self):
        """Test loading non-existent config file"""
        config = Config()
        
        with patch('pathlib.Path.exists', return_value=False):
            result = config.load_config("nonexistent.yaml")
            assert result is False
            assert config.config == Config.DEFAULT_CONFIG

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML file"""
        config = Config()
        
        with patch('builtins.open', mock_open(read_data="invalid: yaml: content:")):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    result = config.load_config("invalid.yaml")
                    assert result is False

    def test_load_invalid_json(self):
        """Test loading invalid JSON file"""
        config = Config()
        
        with patch('builtins.open', mock_open(read_data="{invalid json")):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    result = config.load_config("invalid.json")
                    assert result is False

    def test_load_unsupported_format(self):
        """Test loading unsupported file format"""
        config = Config()
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.is_file', return_value=True):
                result = config.load_config("config.txt")
                assert result is False

    def test_load_file_read_error(self):
        """Test handling file read error"""
        config = Config()
        
        with patch('builtins.open', side_effect=IOError("Read error")):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    result = config.load_config("error.yaml")
                    assert result is False


class TestMergeConfig:
    """Test _merge_config method"""

    def test_merge_simple_values(self):
        """Test merging simple config values"""
        config = Config()
        user_config = {"theme": "custom", "font_family": "Monaco"}
        
        config._merge_config(user_config)
        assert config.config["theme"] == "custom"
        assert config.config["font_family"] == "Monaco"

    def test_merge_nested_dict(self):
        """Test merging nested dictionaries"""
        config = Config()
        user_config = {
            "css": {
                "text_color": "#000",
                "background_color": "#fff"
            }
        }
        
        config._merge_config(user_config)
        assert config.config["css"]["text_color"] == "#000"
        assert config.config["css"]["background_color"] == "#fff"
        # Other CSS values should remain
        assert "max_width" in config.config["css"]

    def test_merge_markers(self):
        """Test merging markers configuration"""
        config = Config()
        user_config = {
            "markers": {
                "カスタム": {"tag": "span", "class": "custom"},
                "太字": {"tag": "b"}  # Override existing
            }
        }
        
        config._merge_config(user_config)
        assert "カスタム" in config.config["markers"]
        assert config.config["markers"]["カスタム"]["tag"] == "span"
        assert config.config["markers"]["太字"]["tag"] == "b"
        # Other markers should remain
        assert "イタリック" in config.config["markers"]

    def test_merge_empty_config(self):
        """Test merging empty config"""
        config = Config()
        original = config.config.copy()
        
        config._merge_config({})
        assert config.config == original

    def test_merge_none_values(self):
        """Test merging with None values"""
        config = Config()
        user_config = {"theme": None, "css": {"text_color": None}}
        
        config._merge_config(user_config)
        # None values should be ignored or handled gracefully


class TestConfigGetters:
    """Test getter methods"""

    def test_get_markers(self):
        """Test getting markers configuration"""
        config = Config()
        markers = config.get_markers()
        
        assert isinstance(markers, dict)
        assert "太字" in markers
        assert "イタリック" in markers
        assert markers["太字"]["tag"] == "strong"

    def test_get_css_variables(self):
        """Test getting CSS variables"""
        config = Config()
        css_vars = config.get_css_variables()
        
        assert isinstance(css_vars, dict)
        assert "--max-width" in css_vars
        assert css_vars["--max-width"] == "800px"
        assert "--text-color" in css_vars
        assert css_vars["--text-color"] == "#333"

    def test_get_theme_name(self):
        """Test getting theme name"""
        config = Config()
        
        # Default theme
        assert config.get_theme_name() == "default"
        
        # Custom theme
        config.config["theme"] = "dark"
        assert config.get_theme_name() == "dark"

    def test_get_theme_name_none(self):
        """Test getting theme name when not set"""
        config = Config()
        config.config.pop("theme", None)
        assert config.get_theme_name() == "default"


class TestValidateConfig:
    """Test config validation"""

    def test_validate_valid_config(self):
        """Test validating valid configuration"""
        config = Config()
        assert config.validate_config() is True

    def test_validate_missing_required_fields(self):
        """Test validating config with missing required fields"""
        config = Config()
        config.config = {}  # Empty config
        assert config.validate_config() is False

    def test_validate_missing_markers(self):
        """Test validating config without markers"""
        config = Config()
        config.config.pop("markers", None)
        assert config.validate_config() is False

    def test_validate_missing_css(self):
        """Test validating config without CSS"""
        config = Config()
        config.config.pop("css", None)
        assert config.validate_config() is False

    def test_validate_invalid_marker_format(self):
        """Test validating invalid marker format"""
        config = Config()
        config.config["markers"]["invalid"] = "not a dict"
        assert config.validate_config() is False

    def test_validate_marker_without_tag(self):
        """Test validating marker without tag"""
        config = Config()
        config.config["markers"]["no_tag"] = {"class": "test"}
        assert config.validate_config() is False


class TestLoadConfigFunction:
    """Test module-level load_config function"""

    def test_load_config_function_default(self):
        """Test load_config function without path"""
        config = load_config()
        assert isinstance(config, Config)
        assert config.config == Config.DEFAULT_CONFIG

    def test_load_config_function_with_path(self):
        """Test load_config function with config path"""
        mock_yaml = {"theme": "custom"}
        
        with patch('builtins.open', mock_open(read_data=yaml.dump(mock_yaml))):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_file', return_value=True):
                    config = load_config("config.yaml")
                    assert isinstance(config, Config)
                    assert config.config["theme"] == "custom"


class TestConfigEdgeCases:
    """Test edge cases and error conditions"""

    def test_config_with_deep_nesting(self):
        """Test config with deeply nested structure"""
        config = Config()
        user_config = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": "value"
                    }
                }
            }
        }
        
        config._merge_config(user_config)
        assert config.config["level1"]["level2"]["level3"]["level4"] == "value"

    def test_config_with_unicode(self):
        """Test config with unicode values"""
        config = Config()
        user_config = {
            "markers": {
                "日本語": {"tag": "span", "class": "japanese"},
                "絵文字": {"tag": "span", "class": "emoji"}
            },
            "theme": "テーマ"
        }
        
        config._merge_config(user_config)
        assert "日本語" in config.config["markers"]
        assert config.config["theme"] == "テーマ"

    def test_config_with_special_characters(self):
        """Test config with special characters"""
        config = Config()
        user_config = {
            "css": {
                "font_family": "'Times New Roman', serif",
                "content": '"Special & Characters < >"'
            }
        }
        
        config._merge_config(user_config)
        assert "Times New Roman" in config.config["css"]["font_family"]

    def test_config_circular_reference(self):
        """Test handling potential circular references"""
        config = Config()
        # Python dicts can't have true circular references
        # But test recursive merge behavior
        user_config = {"a": {"b": {"c": {}}}}
        config._merge_config(user_config)
        assert "a" in config.config

    def test_config_very_large_values(self):
        """Test config with very large values"""
        config = Config()
        user_config = {
            "css": {
                "max_width": "999999px",
                "very_long_key" * 100: "value"
            }
        }
        
        config._merge_config(user_config)
        assert config.config["css"]["max_width"] == "999999px"

    def test_theme_selection_fallback(self):
        """Test theme selection with invalid theme"""
        config = Config()
        config.config["theme"] = "nonexistent_theme"
        
        # Should still return the configured theme name
        assert config.get_theme_name() == "nonexistent_theme"

    def test_css_variables_with_missing_css(self):
        """Test getting CSS variables when CSS config is missing"""
        config = Config()
        config.config.pop("css", None)
        
        css_vars = config.get_css_variables()
        assert isinstance(css_vars, dict)
        # Should return empty or handle gracefully