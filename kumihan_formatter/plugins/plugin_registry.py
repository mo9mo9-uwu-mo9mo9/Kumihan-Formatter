"""Plugin registry for managing plugin types and capabilities

This module provides a central registry for organizing plugins by type
and capability, enabling efficient plugin lookup and selection.
"""

from typing import Dict, List, Optional, Set, Type
from collections import defaultdict

from ..core.common import KumihanError, ErrorCategory
from .plugin_interface import (
    KumihanPlugin, ParserPlugin, RendererPlugin,
    ValidatorPlugin, ProcessorPlugin
)


class PluginRegistry:
    """Central registry for organizing and accessing plugins by capability"""
    
    def __init__(self):
        """Initialize plugin registry"""
        self._plugins_by_type: Dict[Type, Dict[str, KumihanPlugin]] = defaultdict(dict)
        self._plugins_by_format: Dict[str, List[KumihanPlugin]] = defaultdict(list)
        self._plugins_by_name: Dict[str, KumihanPlugin] = {}
        self._enabled_plugins: Set[str] = set()
    
    def register_plugin(self, plugin: KumihanPlugin) -> None:
        """Register a plugin in the registry
        
        Args:
            plugin: Plugin instance to register
            
        Raises:
            KumihanError: If plugin registration fails
        """
        if plugin.name in self._plugins_by_name:
            existing = self._plugins_by_name[plugin.name]
            raise KumihanError(
                f"Plugin '{plugin.name}' already registered",
                category=ErrorCategory.SYSTEM,
                user_message=f"プラグイン '{plugin.name}' は既に登録されています",
                technical_details=f"Existing: {existing.version}, New: {plugin.version}"
            )
        
        # Register by name
        self._plugins_by_name[plugin.name] = plugin
        
        # Register by type
        plugin_type = type(plugin)
        self._plugins_by_type[plugin_type][plugin.name] = plugin
        
        # Register by supported formats
        for format_name in plugin.get_supported_formats():
            self._plugins_by_format[format_name].append(plugin)
        
        # Track enabled status
        if plugin.enabled:
            self._enabled_plugins.add(plugin.name)
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """Unregister a plugin from the registry
        
        Args:
            plugin_name: Name of plugin to unregister
            
        Returns:
            bool: True if unregistered successfully
        """
        if plugin_name not in self._plugins_by_name:
            return False
        
        plugin = self._plugins_by_name[plugin_name]
        
        # Remove from name registry
        del self._plugins_by_name[plugin_name]
        
        # Remove from type registry
        plugin_type = type(plugin)
        if plugin_name in self._plugins_by_type[plugin_type]:
            del self._plugins_by_type[plugin_type][plugin_name]
        
        # Remove from format registry
        for format_name in plugin.get_supported_formats():
            if plugin in self._plugins_by_format[format_name]:
                self._plugins_by_format[format_name].remove(plugin)
        
        # Remove from enabled set
        self._enabled_plugins.discard(plugin_name)
        
        return True
    
    def get_plugin_by_name(self, plugin_name: str) -> Optional[KumihanPlugin]:
        """Get plugin by name
        
        Args:
            plugin_name: Name of plugin to retrieve
            
        Returns:
            Optional[KumihanPlugin]: Plugin instance or None if not found
        """
        return self._plugins_by_name.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: Type[KumihanPlugin]) -> List[KumihanPlugin]:
        """Get all plugins of a specific type
        
        Args:
            plugin_type: Plugin type class
            
        Returns:
            List[KumihanPlugin]: List of plugins of that type
        """
        return list(self._plugins_by_type[plugin_type].values())
    
    def get_parser_plugins(self) -> List[ParserPlugin]:
        """Get all parser plugins
        
        Returns:
            List[ParserPlugin]: List of parser plugins
        """
        return [p for p in self.get_plugins_by_type(ParserPlugin) if isinstance(p, ParserPlugin)]
    
    def get_renderer_plugins(self) -> List[RendererPlugin]:
        """Get all renderer plugins
        
        Returns:
            List[RendererPlugin]: List of renderer plugins
        """
        return [p for p in self.get_plugins_by_type(RendererPlugin) if isinstance(p, RendererPlugin)]
    
    def get_validator_plugins(self) -> List[ValidatorPlugin]:
        """Get all validator plugins
        
        Returns:
            List[ValidatorPlugin]: List of validator plugins
        """
        return [p for p in self.get_plugins_by_type(ValidatorPlugin) if isinstance(p, ValidatorPlugin)]
    
    def get_processor_plugins(self) -> List[ProcessorPlugin]:
        """Get all processor plugins
        
        Returns:
            List[ProcessorPlugin]: List of processor plugins
        """
        return [p for p in self.get_plugins_by_type(ProcessorPlugin) if isinstance(p, ProcessorPlugin)]
    
    def get_plugins_for_format(self, format_name: str) -> List[KumihanPlugin]:
        """Get plugins that support a specific format
        
        Args:
            format_name: Format identifier
            
        Returns:
            List[KumihanPlugin]: List of plugins supporting the format
        """
        return [p for p in self._plugins_by_format[format_name] if p.enabled]
    
    def get_parser_for_format(self, format_name: str) -> Optional[ParserPlugin]:
        """Get the best parser plugin for a format
        
        Args:
            format_name: Format identifier
            
        Returns:
            Optional[ParserPlugin]: Best parser plugin or None
        """
        parsers = [p for p in self.get_plugins_for_format(format_name) if isinstance(p, ParserPlugin)]
        
        if not parsers:
            return None
        
        # Sort by priority (highest first)
        parsers.sort(key=lambda p: p.get_parser_priority(), reverse=True)
        return parsers[0]
    
    def get_renderer_for_format(self, format_name: str) -> Optional[RendererPlugin]:
        """Get renderer plugin for an output format
        
        Args:
            format_name: Output format identifier
            
        Returns:
            Optional[RendererPlugin]: Renderer plugin or None
        """
        renderers = [p for p in self.get_renderer_plugins() if p.get_output_format() == format_name]
        return renderers[0] if renderers else None
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin
        
        Args:
            plugin_name: Name of plugin to enable
            
        Returns:
            bool: True if enabled successfully
        """
        if plugin_name not in self._plugins_by_name:
            return False
        
        plugin = self._plugins_by_name[plugin_name]
        try:
            if not plugin.is_initialized():
                plugin.initialize()
            plugin.enabled = True
            self._enabled_plugins.add(plugin_name)
            return True
        except Exception:
            return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin
        
        Args:
            plugin_name: Name of plugin to disable
            
        Returns:
            bool: True if disabled successfully
        """
        if plugin_name not in self._plugins_by_name:
            return False
        
        plugin = self._plugins_by_name[plugin_name]
        plugin.enabled = False
        self._enabled_plugins.discard(plugin_name)
        return True
    
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """Check if plugin is enabled
        
        Args:
            plugin_name: Plugin name to check
            
        Returns:
            bool: True if enabled
        """
        return plugin_name in self._enabled_plugins
    
    def get_all_plugins(self) -> List[KumihanPlugin]:
        """Get all registered plugins
        
        Returns:
            List[KumihanPlugin]: All registered plugins
        """
        return list(self._plugins_by_name.values())
    
    def get_enabled_plugins(self) -> List[KumihanPlugin]:
        """Get all enabled plugins
        
        Returns:
            List[KumihanPlugin]: All enabled plugins
        """
        return [p for p in self._plugins_by_name.values() if p.enabled]
    
    def get_plugin_count(self) -> Dict[str, int]:
        """Get plugin count statistics
        
        Returns:
            Dict[str, int]: Plugin counts by category
        """
        return {
            'total': len(self._plugins_by_name),
            'enabled': len(self._enabled_plugins),
            'parsers': len(self.get_parser_plugins()),
            'renderers': len(self.get_renderer_plugins()),
            'validators': len(self.get_validator_plugins()),
            'processors': len(self.get_processor_plugins())
        }
    
    def get_supported_formats(self) -> Dict[str, int]:
        """Get supported formats and plugin count
        
        Returns:
            Dict[str, int]: Format names and number of supporting plugins
        """
        formats = {}
        for format_name, plugins in self._plugins_by_format.items():
            enabled_count = sum(1 for p in plugins if p.enabled)
            if enabled_count > 0:
                formats[format_name] = enabled_count
        return formats
    
    def validate_dependencies(self) -> List[KumihanError]:
        """Validate plugin dependencies
        
        Returns:
            List[KumihanError]: Dependency validation errors
        """
        errors = []
        
        for plugin in self._plugins_by_name.values():
            for dependency in plugin.get_dependencies():
                if dependency not in self._plugins_by_name:
                    errors.append(KumihanError(
                        f"Plugin '{plugin.name}' requires missing dependency '{dependency}'",
                        category=ErrorCategory.SYSTEM,
                        user_message=f"プラグイン '{plugin.name}' の依存関係 '{dependency}' が見つかりません"
                    ))
                elif not self.is_plugin_enabled(dependency):
                    errors.append(KumihanError(
                        f"Plugin '{plugin.name}' requires disabled dependency '{dependency}'",
                        category=ErrorCategory.SYSTEM,
                        user_message=f"プラグイン '{plugin.name}' の依存関係 '{dependency}' が無効になっています"
                    ))
        
        return errors
    
    def clear(self) -> None:
        """Clear all registered plugins"""
        self._plugins_by_type.clear()
        self._plugins_by_format.clear()
        self._plugins_by_name.clear()
        self._enabled_plugins.clear()