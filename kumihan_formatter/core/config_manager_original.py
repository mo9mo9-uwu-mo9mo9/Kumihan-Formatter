"""Enhanced configuration management for Kumihan-Formatter

This module provides advanced configuration management with validation,
schema checking, and environment-specific settings.
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class ConfigLevel(Enum):
    """Configuration priority levels"""
    DEFAULT = 1
    SYSTEM = 2
    USER = 3
    PROJECT = 4
    ENVIRONMENT = 5


@dataclass
class ValidationResult:
    """Configuration validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def has_issues(self) -> bool:
        """Check if there are any validation issues"""
        return len(self.errors) > 0 or len(self.warnings) > 0


class ConfigValidator:
    """
    設定値検証・スキーマチェック

    設計ドキュメント:
    - 仕様: /SPEC.md#出力形式オプション
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 設定詳細: /docs/configuration.md

    関連クラス:
    - EnhancedConfig: 検証対象の設定管理クラス
    - ValidationResult: 検証結果の格納

    責務:
    - 設定値の型・範囲チェック
    - 必須項目の存在確認
    - キーワード定義の妥当性検証
    """
    """Advanced configuration validator"""
    
    # Required configuration schema
    SCHEMA = {
        "markers": {
            "type": dict,
            "required": True,
            "schema": {
                "*": {
                    "type": dict,
                    "required_keys": ["tag"],
                    "optional_keys": ["class", "summary"]
                }
            }
        },
        "theme": {
            "type": str,
            "required": False,
            "default": "default"
        },
        "font_family": {
            "type": str,
            "required": False,
            "default": "Hiragino Kaku Gothic ProN, Hiragino Sans, Yu Gothic, Meiryo, sans-serif"
        },
        "css": {
            "type": dict,
            "required": False,
            "schema": {
                "max_width": {"type": str},
                "background_color": {"type": str},
                "container_background": {"type": str},
                "text_color": {"type": str},
                "line_height": {"type": str}
            }
        },
        "themes": {
            "type": dict,
            "required": False,
            "schema": {
                "*": {
                    "type": dict,
                    "required_keys": ["name", "css"],
                    "schema": {
                        "name": {"type": str},
                        "css": {"type": dict}
                    }
                }
            }
        }
    }
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate configuration against schema"""
        errors = []
        warnings = []
        
        # Check required sections
        for key, spec in self.SCHEMA.items():
            if spec.get("required", False) and key not in config:
                errors.append(f"Required section '{key}' is missing")
            elif key in config:
                section_errors, section_warnings = self._validate_section(
                    key, config[key], spec
                )
                errors.extend(section_errors)
                warnings.extend(section_warnings)
        
        # Check for unknown top-level keys
        known_keys = set(self.SCHEMA.keys())
        unknown_keys = set(config.keys()) - known_keys
        for key in unknown_keys:
            warnings.append(f"Unknown configuration key: '{key}'")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_section(self, section_name: str, section_data: Any, 
                         spec: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Validate a configuration section"""
        errors = []
        warnings = []
        
        # Type validation
        expected_type = spec.get("type")
        if expected_type and not isinstance(section_data, expected_type):
            errors.append(f"Section '{section_name}' must be of type {expected_type.__name__}")
            return errors, warnings
        
        # Schema validation for dict types
        if expected_type == dict and "schema" in spec:
            schema = spec["schema"]
            
            # Handle wildcard schemas
            if "*" in schema:
                wildcard_spec = schema["*"]
                for key, value in section_data.items():
                    key_errors, key_warnings = self._validate_section(
                        f"{section_name}.{key}", value, wildcard_spec
                    )
                    errors.extend(key_errors)
                    warnings.extend(key_warnings)
            else:
                # Handle specific key schemas
                for key, sub_spec in schema.items():
                    if key in section_data:
                        key_errors, key_warnings = self._validate_section(
                            f"{section_name}.{key}", section_data[key], sub_spec
                        )
                        errors.extend(key_errors)
                        warnings.extend(key_warnings)
        
        # Required keys validation
        if "required_keys" in spec and isinstance(section_data, dict):
            for required_key in spec["required_keys"]:
                if required_key not in section_data:
                    errors.append(f"Required key '{required_key}' missing in {section_name}")
        
        return errors, warnings


class EnhancedConfig:
    """
    拡張設定管理（複数設定ソース統合・環境別設定）

    設計ドキュメント:
    - 仕様: /SPEC.md#出力形式オプション
    - アーキテクチャ: /CONTRIBUTING.md#アーキテクチャ概要
    - 設定詳細: /docs/configuration.md

    関連クラス:
    - ConfigValidator: 設定値の検証
    - Parser: 設定を使用する主要クラス
    - Renderer: 設定に基づくHTML生成

    責務:
    - 設定ファイルの読み込み・マージ
    - 環境変数による設定上書き
    - デフォルト値の提供
    - 設定値へのアクセスインターフェース
    """
    """Enhanced configuration manager with advanced features"""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "markers": {
            "太字": {"tag": "strong"},
            "イタリック": {"tag": "em"},
            "枠線": {"tag": "div", "class": "box"},
            "ハイライト": {"tag": "div", "class": "highlight"},
            "見出し1": {"tag": "h1"},
            "見出し2": {"tag": "h2"},
            "見出し3": {"tag": "h3"},
            "見出し4": {"tag": "h4"},
            "見出し5": {"tag": "h5"},
            "折りたたみ": {"tag": "details", "summary": "詳細を表示"},
            "ネタバレ": {"tag": "details", "summary": "ネタバレを表示"},
        },
        "theme": "default",
        "font_family": "Hiragino Kaku Gothic ProN, Hiragino Sans, Yu Gothic, Meiryo, sans-serif",
        "css": {
            "max_width": "800px",
            "background_color": "#f9f9f9",
            "container_background": "white",
            "text_color": "#333",
            "line_height": "1.8"
        },
        "themes": {
            "default": {
                "name": "デフォルト",
                "css": {
                    "background_color": "#f9f9f9",
                    "container_background": "white",
                    "text_color": "#333"
                }
            },
            "dark": {
                "name": "ダーク",
                "css": {
                    "background_color": "#1a1a1a",
                    "container_background": "#2d2d2d",
                    "text_color": "#e0e0e0"
                }
            },
            "sepia": {
                "name": "セピア", 
                "css": {
                    "background_color": "#f4f1ea",
                    "container_background": "#fdf6e3",
                    "text_color": "#5c4b37"
                }
            },
            "high-contrast": {
                "name": "ハイコントラスト",
                "css": {
                    "background_color": "#000000",
                    "container_background": "#ffffff", 
                    "text_color": "#000000"
                }
            }
        },
        "performance": {
            "max_recursion_depth": 50,
            "max_nodes": 10000,
            "cache_templates": True
        },
        "validation": {
            "strict_mode": False,
            "warn_unknown_keywords": True,
            "max_file_size_mb": 10
        }
    }
    
    def __init__(self):
        self.config = {}
        self.config_sources = {}  # Track where each config value came from
        self.validator = ConfigValidator()
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default configuration"""
        self.config = self._deep_copy(self.DEFAULT_CONFIG)
        self._mark_source("default", self.config)
    
    def _deep_copy(self, obj: Any) -> Any:
        """Deep copy utility"""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj
    
    def _mark_source(self, source: str, obj: Any, path: str = ""):
        """Mark configuration source for tracking"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                self.config_sources[current_path] = source
                self._mark_source(source, value, current_path)
    
    def load_from_file(self, config_path: Union[str, Path], level: ConfigLevel = ConfigLevel.USER) -> bool:
        """Load configuration from file"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            logging.warning(f"Configuration file not found: {config_path}")
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    if not HAS_YAML:
                        logging.error("YAML support not available. Install PyYAML to use YAML config files.")
                        return False
                    user_config = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    user_config = json.load(f)
                else:
                    logging.error(f"Unsupported config format: {config_path.suffix}")
                    return False
            
            if not isinstance(user_config, dict):
                logging.error("Configuration file must contain a dictionary")
                return False
            
            # Validate before merging
            validation_result = self.validator.validate(user_config)
            if not validation_result.is_valid:
                logging.error(f"Configuration validation failed: {validation_result.errors}")
                return False
            
            # Log warnings
            for warning in validation_result.warnings:
                logging.warning(f"Configuration warning: {warning}")
            
            self._merge_config(user_config, str(config_path))
            logging.info(f"Loaded configuration from: {config_path}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to load configuration from {config_path}: {e}")
            return False
    
    def load_from_environment(self) -> bool:
        """Load configuration from environment variables"""
        env_config = {}
        
        # Map environment variables to config paths
        env_mappings = {
            "KUMIHAN_THEME": "theme",
            "KUMIHAN_FONT_FAMILY": "font_family",
            "KUMIHAN_MAX_WIDTH": "css.max_width",
            "KUMIHAN_BACKGROUND_COLOR": "css.background_color",
            "KUMIHAN_TEXT_COLOR": "css.text_color",
            "KUMIHAN_STRICT_MODE": "validation.strict_mode",
        }
        
        for env_var, config_path in env_mappings.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                
                # Type conversion for boolean values
                if config_path.endswith("strict_mode"):
                    value = value.lower() in ("true", "1", "yes", "on")
                
                self._set_nested_value(env_config, config_path, value)
        
        if env_config:
            self._merge_config(env_config, "environment")
            logging.info("Loaded configuration from environment variables")
            return True
        
        return False
    
    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Set a nested configuration value using dot notation"""
        keys = path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _merge_config(self, user_config: Dict[str, Any], source: str):
        """Merge user configuration into current config"""
        def merge_recursive(target: Dict[str, Any], source_dict: Dict[str, Any], path: str = ""):
            for key, value in source_dict.items():
                current_path = f"{path}.{key}" if path else key
                
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    merge_recursive(target[key], value, current_path)
                else:
                    target[key] = value
                    self.config_sources[current_path] = source
        
        merge_recursive(self.config, user_config)
    
    def get_markers(self) -> Dict[str, Dict[str, Any]]:
        """Get marker definitions"""
        return self.config.get("markers", {})
    
    def get_css_variables(self) -> Dict[str, str]:
        """Get CSS variables for template rendering"""
        css_vars = self.config.get("css", {}).copy()
        css_vars["font_family"] = self.config.get("font_family", "")
        
        # Apply theme CSS if theme is set
        theme = self.config.get("theme", "default")
        themes = self.config.get("themes", {})
        if theme in themes and "css" in themes[theme]:
            css_vars.update(themes[theme]["css"])
        
        return css_vars
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance-related settings"""
        return self.config.get("performance", {})
    
    def get_validation_settings(self) -> Dict[str, Any]:
        """Get validation settings"""
        return self.config.get("validation", {})
    
    def validate(self) -> ValidationResult:
        """Validate current configuration"""
        return self.validator.validate(self.config)
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get configuration metadata and source information"""
        return {
            "sources": self.config_sources,
            "validation": self.validate(),
            "theme_name": self.get_theme_name(),
            "marker_count": len(self.get_markers()),
            "theme_count": len(self.config.get("themes", {}))
        }
    
    def get_theme_name(self) -> str:
        """Get current theme display name"""
        theme_key = self.config.get("theme", "default")
        themes = self.config.get("themes", {})
        return themes.get(theme_key, {}).get("name", "Unknown")
    
    def export_config(self, format_type: str = "json") -> str:
        """Export current configuration"""
        if format_type.lower() == "yaml":
            if not HAS_YAML:
                raise ValueError("YAML export not available. Install PyYAML for YAML support.")
            return yaml.dump(self.config, default_flow_style=False, allow_unicode=True)
        elif format_type.lower() == "json":
            return json.dumps(self.config, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


def load_enhanced_config(config_path: Optional[str] = None) -> EnhancedConfig:
    """Load enhanced configuration with automatic environment detection"""
    config = EnhancedConfig()
    
    # Load from environment variables first
    config.load_from_environment()
    
    # Load from file if specified
    if config_path:
        config.load_from_file(config_path)
    else:
        # Try to find config files in standard locations
        possible_paths = [
            Path("kumihan.yaml"),
            Path("kumihan.yml"), 
            Path("kumihan.json"),
            Path.home() / ".kumihan" / "config.yaml",
            Path.home() / ".config" / "kumihan" / "config.yaml"
        ]
        
        for path in possible_paths:
            if path.exists():
                config.load_from_file(path)
                break
    
    return config