"""Configuration service implementation

This module provides centralized configuration management with
support for multiple sources, validation, and hot reloading.
"""

import json
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from ..core.interfaces import ConfigurationService
from ..core.common import (
    KumihanError, ErrorCategory, ValidationMixin, 
    get_cache, SmartCache
)


class ConfigurationServiceImpl(ConfigurationService, ValidationMixin):
    """Centralized configuration service implementation
    
    Features:
    - Multiple configuration sources (files, environment, defaults)
    - Dot notation for nested access
    - Configuration validation
    - Hot reloading
    - Caching for performance
    """
    
    def __init__(self, cache_enabled: bool = True):
        """Initialize configuration service
        
        Args:
            cache_enabled: Whether to enable configuration caching
        """
        super().__init__()
        
        self._config: Dict[str, Any] = {}
        self._sources: List[Dict[str, Any]] = []
        self._file_paths: List[Path] = []
        self._last_modified: Dict[Path, datetime] = {}
        
        # Setup caching
        if cache_enabled:
            self._cache: Optional[SmartCache] = get_cache("configuration")
        else:
            self._cache = None
        
        # Setup validation rules
        self._setup_validation_rules()
        
        # Load default configuration
        self._load_defaults()
    
    def _setup_validation_rules(self) -> None:
        """Setup configuration validation rules"""
        # Core configuration validation
        self.require_type("debug", bool)
        self.require_type("cache.enabled", bool)
        self.require_type("cache.ttl", int)
        self.require_in_range("cache.ttl", min_val=1, max_val=86400)  # 1 second to 1 day
        
        # Parser configuration
        self.require_type("parser.strict_mode", bool)
        self.require_type("parser.max_file_size_mb", int)
        self.require_in_range("parser.max_file_size_mb", min_val=1, max_val=100)
        
        # Renderer configuration
        self.require_one_of("renderer.output_format", ["html", "pdf", "epub"])
        self.require_type("renderer.pretty_print", bool)
        
        # Plugin configuration
        self.require_type("plugins.auto_load", bool)
        self.require_type("plugins.directories", list)
    
    def _load_defaults(self) -> None:
        """Load default configuration values"""
        defaults = {
            "debug": False,
            "cache": {
                "enabled": True,
                "ttl": 3600,
                "max_entries": 1000
            },
            "parser": {
                "strict_mode": False,
                "max_file_size_mb": 10,
                "encoding": "utf-8"
            },
            "renderer": {
                "output_format": "html",
                "pretty_print": True,
                "minify_html": False
            },
            "plugins": {
                "auto_load": True,
                "directories": []
            },
            "ui": {
                "color_output": True,
                "progress_bars": True,
                "verbose": False
            }
        }
        
        self._config = defaults
        self._sources.append({"type": "defaults", "data": defaults})
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        # Check cache first
        if self._cache:
            cache_key = f"config:{key}"
            cached_value = self._cache.get(cache_key)
            if cached_value is not None:
                return cached_value
        
        # Navigate nested dictionaries using dot notation
        keys = key.split('.')
        current = self._config
        
        try:
            for k in keys:
                current = current[k]
            
            # Cache the result if caching is enabled
            if self._cache:
                self._cache.set(cache_key, current, ttl=300)  # 5 minutes
            
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        # Validate the value if we have a validation rule
        try:
            validation_data = {key: value}
            errors = self.validate_all(validation_data)
            if errors:
                raise KumihanError(
                    f"Invalid configuration value for '{key}'",
                    category=ErrorCategory.CONFIGURATION,
                    user_message=f"設定値 '{key}' が無効です",
                    suggestions=[error.message for error in errors]
                )
        except Exception:
            # If validation fails, we'll allow the set but warn
            pass
        
        # Navigate and set nested value
        keys = key.split('.')
        current = self._config
        
        # Navigate to parent of target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                # Convert non-dict to dict
                current[k] = {}
            current = current[k]
        
        # Set the final value
        current[keys[-1]] = value
        
        # Invalidate cache
        if self._cache:
            cache_key = f"config:{key}"
            self._cache.remove(cache_key)
        
        # Add to sources
        self._sources.append({
            "type": "manual",
            "data": {key: value},
            "timestamp": datetime.now()
        })
    
    def load_from_file(self, file_path: Path) -> bool:
        """Load configuration from file
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            if not file_path.exists():
                raise KumihanError(
                    f"Configuration file not found: {file_path}",
                    category=ErrorCategory.FILE_SYSTEM,
                    user_message=f"設定ファイルが見つかりません: {file_path}"
                )
            
            # Determine file format from extension
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                if not HAS_YAML:
                    raise KumihanError(
                        "YAML support not available",
                        category=ErrorCategory.CONFIGURATION,
                        user_message="YAML サポートが利用できません",
                        suggestions=["pip install pyyaml を実行してください"]
                    )
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
            else:
                raise KumihanError(
                    f"Unsupported configuration file format: {file_path.suffix}",
                    category=ErrorCategory.CONFIGURATION,
                    user_message=f"サポートされていない設定ファイル形式: {file_path.suffix}",
                    suggestions=["YAML (.yaml/.yml) または JSON (.json) ファイルを使用してください"]
                )
            
            if not isinstance(file_config, dict):
                raise KumihanError(
                    "Configuration file must contain a dictionary/object",
                    category=ErrorCategory.CONFIGURATION,
                    user_message="設定ファイルは辞書/オブジェクト形式である必要があります"
                )
            
            # Merge with existing configuration
            self._deep_merge(self._config, file_config)
            
            # Track file and modification time
            self._file_paths.append(file_path)
            self._last_modified[file_path] = datetime.fromtimestamp(file_path.stat().st_mtime)
            
            # Add to sources
            self._sources.append({
                "type": "file",
                "path": str(file_path),
                "data": file_config,
                "timestamp": datetime.now()
            })
            
            # Clear cache on reload
            if self._cache:
                self._cache.clear()
            
            return True
        
        except Exception as e:
            if isinstance(e, KumihanError):
                raise
            
            raise KumihanError(
                f"Failed to load configuration from {file_path}",
                category=ErrorCategory.CONFIGURATION,
                cause=e,
                user_message=f"設定ファイル {file_path} の読み込みに失敗しました"
            )
    
    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep merge source dictionary into target"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value
    
    def validate_configuration(self) -> List[KumihanError]:
        """Validate current configuration
        
        Returns:
            List[KumihanError]: Validation errors (empty if valid)
        """
        return self.validate_all(self._config)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary
        
        Returns:
            Dict[str, Any]: All configuration values
        """
        return self._config.copy()
    
    def reload_files(self) -> bool:
        """Reload configuration from all tracked files
        
        Returns:
            bool: True if all files reloaded successfully
        """
        success = True
        
        for file_path in self._file_paths:
            try:
                # Check if file has been modified
                if file_path.exists():
                    current_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    last_mtime = self._last_modified.get(file_path)
                    
                    if last_mtime and current_mtime > last_mtime:
                        # File has been modified, reload it
                        if not self.load_from_file(file_path):
                            success = False
                else:
                    # File no longer exists
                    print(f"Warning: Configuration file no longer exists: {file_path}")
                    success = False
            
            except Exception as e:
                print(f"Warning: Failed to reload configuration from {file_path}: {e}")
                success = False
        
        return success
    
    def get_configuration_sources(self) -> List[Dict[str, Any]]:
        """Get information about configuration sources
        
        Returns:
            List[Dict[str, Any]]: Source information
        """
        return self._sources.copy()
    
    def export_configuration(self, file_path: Path, format: str = "yaml") -> bool:
        """Export current configuration to file
        
        Args:
            file_path: Output file path
            format: Output format ('yaml' or 'json')
            
        Returns:
            bool: True if exported successfully
        """
        try:
            if format.lower() == "yaml":
                if not HAS_YAML:
                    raise ValueError("YAML support not available")
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            elif format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            return True
        
        except Exception as e:
            raise KumihanError(
                f"Failed to export configuration to {file_path}",
                category=ErrorCategory.FILE_SYSTEM,
                cause=e,
                user_message=f"設定の出力に失敗しました: {file_path}"
            )
    
    def has_key(self, key: str) -> bool:
        """Check if configuration key exists
        
        Args:
            key: Configuration key (supports dot notation)
            
        Returns:
            bool: True if key exists
        """
        keys = key.split('.')
        current = self._config
        
        try:
            for k in keys:
                current = current[k]
            return True
        except (KeyError, TypeError):
            return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section
        
        Args:
            section: Section name
            
        Returns:
            Dict[str, Any]: Section configuration
        """
        value = self.get(section, {})
        return value if isinstance(value, dict) else {}
    
    def clear_cache(self) -> None:
        """Clear configuration cache"""
        if self._cache:
            self._cache.clear()
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics
        
        Returns:
            Optional[Dict[str, Any]]: Cache stats or None if caching disabled
        """
        if self._cache:
            return self._cache.get_stats()
        return None