"""Plugin loading and discovery system

This module handles the discovery, loading, and instantiation of plugins
from various sources including files, directories, and packages.
"""

import importlib
import importlib.util
import inspect
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ..core.common import ErrorCategory, ErrorSeverity, KumihanError
from .plugin_interface import KumihanPlugin, PluginMetadata


class PluginLoader:
    """Loads and manages plugin discovery and instantiation"""

    def __init__(self):
        """Initialize plugin loader"""
        self.discovered_plugins: Dict[str, PluginMetadata] = {}
        self.loaded_plugins: Dict[str, KumihanPlugin] = {}
        self._search_paths: List[Path] = []

    def add_search_path(self, path: Path) -> None:
        """Add a directory to search for plugins

        Args:
            path: Directory path to search
        """
        if path.exists() and path.is_dir():
            self._search_paths.append(path)

    def discover_plugins(self, search_paths: Optional[List[Path]] = None) -> List[PluginMetadata]:
        """Discover plugins in search paths

        Args:
            search_paths: Optional list of paths to search

        Returns:
            List[PluginMetadata]: Discovered plugin metadata
        """
        paths_to_search = search_paths or self._search_paths
        discovered = []

        for path in paths_to_search:
            if path.is_file() and path.suffix == ".py":
                # Single plugin file
                metadata = self._discover_plugin_file(path)
                if metadata:
                    discovered.append(metadata)
            elif path.is_dir():
                # Directory with plugin files
                discovered.extend(self._discover_plugin_directory(path))

        # Update discovered plugins registry
        for metadata in discovered:
            self.discovered_plugins[metadata.name] = metadata

        return discovered

    def _discover_plugin_file(self, file_path: Path) -> Optional[PluginMetadata]:
        """Discover plugin in a single file

        Args:
            file_path: Path to Python file

        Returns:
            Optional[PluginMetadata]: Plugin metadata if found
        """
        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location(f"plugin_{file_path.stem}", file_path)
            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin classes
            plugin_classes = self._find_plugin_classes(module)

            if plugin_classes:
                # Use first plugin class found
                plugin_class = plugin_classes[0]

                # Get plugin metadata
                name = getattr(plugin_class, "PLUGIN_NAME", plugin_class.__name__)
                version = getattr(plugin_class, "PLUGIN_VERSION", "1.0.0")

                return PluginMetadata(name=name, version=version, plugin_class=plugin_class, file_path=file_path)

        except Exception as e:
            # Log error but don't fail discovery
            print(f"Warning: Failed to discover plugin in {file_path}: {e}")
            return None

    def _discover_plugin_directory(self, dir_path: Path) -> List[PluginMetadata]:
        """Discover plugins in a directory

        Args:
            dir_path: Directory to search

        Returns:
            List[PluginMetadata]: Found plugin metadata
        """
        discovered = []

        # Look for Python files
        for py_file in dir_path.glob("*.py"):
            if py_file.name.startswith("__"):
                continue  # Skip __init__.py, __pycache__, etc.

            metadata = self._discover_plugin_file(py_file)
            if metadata:
                discovered.append(metadata)

        # Look for plugin packages (directories with __init__.py)
        for sub_dir in dir_path.iterdir():
            if sub_dir.is_dir() and (sub_dir / "__init__.py").exists():
                try:
                    # Try to import as package
                    spec = importlib.util.spec_from_file_location(sub_dir.name, sub_dir / "__init__.py")
                    if not spec or not spec.loader:
                        continue

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    plugin_classes = self._find_plugin_classes(module)
                    for plugin_class in plugin_classes:
                        name = getattr(plugin_class, "PLUGIN_NAME", plugin_class.__name__)
                        version = getattr(plugin_class, "PLUGIN_VERSION", "1.0.0")

                        discovered.append(
                            PluginMetadata(name=name, version=version, plugin_class=plugin_class, file_path=sub_dir)
                        )

                except Exception as e:
                    print(f"Warning: Failed to discover plugin package in {sub_dir}: {e}")
                    continue

        return discovered

    def _find_plugin_classes(self, module) -> List[Type[KumihanPlugin]]:
        """Find plugin classes in a module

        Args:
            module: Python module to search

        Returns:
            List[Type[KumihanPlugin]]: Found plugin classes
        """
        plugin_classes = []

        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Skip imported classes and base classes
            if obj.__module__ != module.__name__:
                continue

            # Check if it's a plugin class
            if issubclass(obj, KumihanPlugin) and obj != KumihanPlugin and not inspect.isabstract(obj):
                plugin_classes.append(obj)

        return plugin_classes

    def load_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> KumihanPlugin:
        """Load and instantiate a plugin

        Args:
            plugin_name: Name of plugin to load
            config: Optional configuration for plugin

        Returns:
            KumihanPlugin: Loaded plugin instance

        Raises:
            KumihanError: If plugin loading fails
        """
        if plugin_name in self.loaded_plugins:
            return self.loaded_plugins[plugin_name]

        if plugin_name not in self.discovered_plugins:
            raise KumihanError(
                f"Plugin '{plugin_name}' not found",
                category=ErrorCategory.SYSTEM,
                user_message=f"プラグイン '{plugin_name}' が見つかりません",
                suggestions=["プラグインが正しくインストールされているか確認してください"],
            )

        metadata = self.discovered_plugins[plugin_name]

        try:
            # Instantiate plugin
            # Try to determine constructor parameters
            sig = inspect.signature(metadata.plugin_class.__init__)
            params = list(sig.parameters.keys())[1:]  # Skip 'self'

            # Provide default values for name and version if needed
            kwargs = {}
            if "name" in params:
                kwargs["name"] = metadata.name
            if "version" in params:
                kwargs["version"] = metadata.version

            plugin = metadata.plugin_class(**kwargs)

            # Configure plugin if config provided
            if config:
                plugin.configure(config)

            # Initialize plugin
            if not plugin.initialize():
                raise KumihanError(f"Plugin '{plugin_name}' initialization failed", category=ErrorCategory.SYSTEM)

            # Store loaded plugin
            self.loaded_plugins[plugin_name] = plugin
            metadata.instance = plugin
            metadata.loaded = True

            return plugin

        except Exception as e:
            raise KumihanError(
                f"Failed to load plugin '{plugin_name}'",
                category=ErrorCategory.SYSTEM,
                cause=e,
                user_message=f"プラグイン '{plugin_name}' の読み込みに失敗しました",
                suggestions=[
                    "プラグインファイルに構文エラーがないか確認してください",
                    "必要な依存関係がインストールされているか確認してください",
                ],
            )

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            bool: True if unloaded successfully
        """
        if plugin_name not in self.loaded_plugins:
            return False

        try:
            plugin = self.loaded_plugins[plugin_name]
            plugin.shutdown()

            del self.loaded_plugins[plugin_name]

            if plugin_name in self.discovered_plugins:
                metadata = self.discovered_plugins[plugin_name]
                metadata.instance = None
                metadata.loaded = False

            return True

        except Exception as e:
            print(f"Warning: Error unloading plugin '{plugin_name}': {e}")
            return False

    def get_loaded_plugins(self) -> Dict[str, KumihanPlugin]:
        """Get all loaded plugins

        Returns:
            Dict[str, KumihanPlugin]: Loaded plugins by name
        """
        return self.loaded_plugins.copy()

    def get_discovered_plugins(self) -> Dict[str, PluginMetadata]:
        """Get all discovered plugins

        Returns:
            Dict[str, PluginMetadata]: Discovered plugins by name
        """
        return self.discovered_plugins.copy()

    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if plugin is loaded

        Args:
            plugin_name: Plugin name to check

        Returns:
            bool: True if loaded
        """
        return plugin_name in self.loaded_plugins

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive plugin information

        Args:
            plugin_name: Plugin name

        Returns:
            Optional[Dict[str, Any]]: Plugin information or None if not found
        """
        if plugin_name in self.discovered_plugins:
            metadata = self.discovered_plugins[plugin_name]
            info = metadata.to_dict()

            # Add runtime information if loaded
            if metadata.instance:
                info.update(metadata.instance.get_plugin_info())

            return info

        return None
