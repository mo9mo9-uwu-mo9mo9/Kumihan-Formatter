"""Plugin manager for coordinating the entire plugin system

This module provides the main interface for managing plugins,
coordinating discovery, loading, and lifecycle management.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..core.interfaces import BaseManager
from ..core.common import KumihanError, ErrorCategory, get_cache
from .plugin_loader import PluginLoader
from .plugin_registry import PluginRegistry
from .plugin_interface import KumihanPlugin


class PluginManager(BaseManager):
    """Main plugin management system
    
    Coordinates plugin discovery, loading, registration, and lifecycle.
    """
    
    def __init__(self, cache_plugins: bool = True):
        """Initialize plugin manager
        
        Args:
            cache_plugins: Whether to cache plugin discovery results
        """
        super().__init__("PluginManager")
        
        self.loader = PluginLoader()
        self.registry = PluginRegistry()
        self.cache_plugins = cache_plugins
        
        if cache_plugins:
            self.cache = get_cache("plugins")
        else:
            self.cache = None
        
        self._plugin_directories: Set[Path] = set()
        self._auto_load: bool = False
    
    def initialize(self) -> bool:
        """Initialize the plugin manager"""
        try:
            # Add default plugin directories
            self._add_default_search_paths()
            
            # Discover plugins if auto-load is enabled
            if self._auto_load:
                self.discover_and_load_plugins()
            
            self._initialized = True
            return True
        
        except Exception as e:
            raise KumihanError(
                "Failed to initialize plugin manager",
                category=ErrorCategory.SYSTEM,
                cause=e
            )
    
    def shutdown(self) -> bool:
        """Shutdown the plugin manager"""
        try:
            # Unload all plugins
            for plugin_name in list(self.registry.get_all_plugins()):
                self.unload_plugin(plugin_name.name)
            
            # Clear registry
            self.registry.clear()
            
            # Clear cache if enabled
            if self.cache:
                self.cache.clear()
            
            self._initialized = False
            return True
        
        except Exception as e:
            raise KumihanError(
                "Failed to shutdown plugin manager",
                category=ErrorCategory.SYSTEM,
                cause=e
            )
    
    def _add_default_search_paths(self) -> None:
        """Add default plugin search paths"""
        # Current package plugins directory
        package_plugins = Path(__file__).parent / "builtin"
        if package_plugins.exists():
            self.add_plugin_directory(package_plugins)
        
        # User plugins directory
        user_plugins = Path.home() / ".kumihan" / "plugins"
        if user_plugins.exists():
            self.add_plugin_directory(user_plugins)
        
        # System plugins directory (relative to project)
        project_root = Path(__file__).parent.parent.parent.parent
        system_plugins = project_root / "plugins"
        if system_plugins.exists():
            self.add_plugin_directory(system_plugins)
    
    def add_plugin_directory(self, directory: Path) -> None:
        """Add a directory to search for plugins
        
        Args:
            directory: Directory path to add
            
        Raises:
            KumihanError: If directory is invalid
        """
        if not directory.exists():
            raise KumihanError(
                f"Plugin directory does not exist: {directory}",
                category=ErrorCategory.FILE_SYSTEM,
                user_message=f"プラグインディレクトリが見つかりません: {directory}"
            )
        
        if not directory.is_dir():
            raise KumihanError(
                f"Plugin path is not a directory: {directory}",
                category=ErrorCategory.FILE_SYSTEM,
                user_message=f"プラグインパスがディレクトリではありません: {directory}"
            )
        
        self._plugin_directories.add(directory)
        self.loader.add_search_path(directory)
    
    def discover_plugins(self, force_refresh: bool = False) -> List[str]:
        """Discover plugins in all search paths
        
        Args:
            force_refresh: Force rediscovery even if cached
            
        Returns:
            List[str]: List of discovered plugin names
        """
        cache_key = "discovered_plugins"
        
        # Check cache first if enabled
        if self.cache and not force_refresh:
            cached_result = self.cache.get(cache_key)
            if cached_result:
                return cached_result
        
        # Discover plugins
        search_paths = list(self._plugin_directories)
        discovered_metadata = self.loader.discover_plugins(search_paths)
        
        plugin_names = [metadata.name for metadata in discovered_metadata]
        
        # Cache results if enabled
        if self.cache:
            self.cache.set(cache_key, plugin_names, ttl=300)  # 5 minutes
        
        return plugin_names
    
    def load_plugin(
        self,
        plugin_name: str,
        config: Optional[Dict[str, Any]] = None,
        enable_immediately: bool = True
    ) -> KumihanPlugin:
        """Load and register a plugin
        
        Args:
            plugin_name: Name of plugin to load
            config: Optional configuration for plugin
            enable_immediately: Whether to enable plugin after loading
            
        Returns:
            KumihanPlugin: Loaded plugin instance
            
        Raises:
            KumihanError: If loading fails
        """
        # Check if already loaded
        existing = self.registry.get_plugin_by_name(plugin_name)
        if existing:
            return existing
        
        # Load plugin
        plugin = self.loader.load_plugin(plugin_name, config)
        
        # Register with registry
        self.registry.register_plugin(plugin)
        
        # Enable if requested
        if enable_immediately and not plugin.enabled:
            self.registry.enable_plugin(plugin_name)
        
        return plugin
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            bool: True if unloaded successfully
        """
        # Unregister from registry
        success = self.registry.unregister_plugin(plugin_name)
        
        # Unload from loader
        if success:
            self.loader.unload_plugin(plugin_name)
        
        return success
    
    def get_plugin(self, plugin_name: str) -> Optional[KumihanPlugin]:
        """Get a loaded plugin by name
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            Optional[KumihanPlugin]: Plugin instance or None
        """
        return self.registry.get_plugin_by_name(plugin_name)
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            bool: True if enabled successfully
        """
        return self.registry.enable_plugin(plugin_name)
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin
        
        Args:
            plugin_name: Plugin name
            
        Returns:
            bool: True if disabled successfully
        """
        return self.registry.disable_plugin(plugin_name)
    
    def list_plugins(self, enabled_only: bool = False) -> Dict[str, Dict[str, Any]]:
        """List all plugins with their information
        
        Args:
            enabled_only: Only include enabled plugins
            
        Returns:
            Dict[str, Dict[str, Any]]: Plugin information by name
        """
        plugins = self.registry.get_enabled_plugins() if enabled_only else self.registry.get_all_plugins()
        
        result = {}
        for plugin in plugins:
            result[plugin.name] = plugin.get_plugin_info()
        
        return result
    
    def get_plugins_for_format(self, format_name: str) -> List[KumihanPlugin]:
        """Get plugins that support a specific format
        
        Args:
            format_name: Format identifier
            
        Returns:
            List[KumihanPlugin]: Supporting plugins
        """
        return self.registry.get_plugins_for_format(format_name)
    
    def discover_and_load_plugins(self, auto_enable: bool = True) -> Dict[str, bool]:
        """Discover and load all found plugins
        
        Args:
            auto_enable: Whether to enable plugins after loading
            
        Returns:
            Dict[str, bool]: Plugin names and their load success status
        """
        discovered = self.discover_plugins()
        results = {}
        
        for plugin_name in discovered:
            try:
                self.load_plugin(plugin_name, enable_immediately=auto_enable)
                results[plugin_name] = True
            except Exception as e:
                print(f"Warning: Failed to load plugin '{plugin_name}': {e}")
                results[plugin_name] = False
        
        return results
    
    def validate_all_plugins(self) -> List[KumihanError]:
        """Validate all loaded plugins
        
        Returns:
            List[KumihanError]: Validation errors
        """
        errors = []
        
        # Check dependencies
        dependency_errors = self.registry.validate_dependencies()
        errors.extend(dependency_errors)
        
        # Validate individual plugins
        for plugin in self.registry.get_all_plugins():
            try:
                plugin_errors = plugin.validate_configuration(plugin.get_configuration())
                errors.extend(plugin_errors)
            except Exception as e:
                errors.append(KumihanError(
                    f"Plugin '{plugin.name}' validation failed",
                    category=ErrorCategory.SYSTEM,
                    cause=e
                ))
        
        return errors
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get plugin system statistics
        
        Returns:
            Dict[str, Any]: Plugin statistics
        """
        plugin_counts = self.registry.get_plugin_count()
        supported_formats = self.registry.get_supported_formats()
        
        return {
            'plugin_counts': plugin_counts,
            'supported_formats': supported_formats,
            'search_paths': [str(p) for p in self._plugin_directories],
            'cache_enabled': self.cache is not None,
            'auto_load_enabled': self._auto_load
        }
    
    def set_auto_load(self, enabled: bool) -> None:
        """Enable or disable automatic plugin loading
        
        Args:
            enabled: Whether to enable auto-loading
        """
        self._auto_load = enabled