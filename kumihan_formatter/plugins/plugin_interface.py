"""Plugin interface definitions

This module defines the interfaces that plugins must implement
to integrate with the Kumihan-Formatter system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pathlib import Path

from ..core.interfaces import (
    BaseParser, BaseRenderer, BaseValidator, BaseProcessor,
    Configurable, Lifecycle
)
from ..core.common import KumihanError


class KumihanPlugin(Configurable, Lifecycle):
    """Base interface for all Kumihan-Formatter plugins
    
    All plugins must implement this interface to be loaded by the plugin system.
    """
    
    def __init__(self, name: str, version: str):
        """Initialize plugin
        
        Args:
            name: Plugin name (should be unique)
            version: Plugin version (semantic versioning recommended)
        """
        self.name = name
        self.version = version
        self.enabled = False
        self._config: Dict[str, Any] = {}
        self._status = "uninitialized"
    
    @abstractmethod
    def get_description(self) -> str:
        """Get plugin description
        
        Returns:
            str: Human-readable description of what this plugin does
        """
        pass
    
    @abstractmethod
    def get_author(self) -> str:
        """Get plugin author information
        
        Returns:
            str: Author name/contact information
        """
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Get list of plugin dependencies
        
        Returns:
            List[str]: List of required plugin names
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Get list of formats this plugin supports
        
        Returns:
            List[str]: List of file extensions or format names
        """
        pass
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get comprehensive plugin information
        
        Returns:
            Dict with plugin metadata
        """
        return {
            'name': self.name,
            'version': self.version,
            'description': self.get_description(),
            'author': self.get_author(),
            'dependencies': self.get_dependencies(),
            'supported_formats': self.get_supported_formats(),
            'enabled': self.enabled,
            'status': self._status
        }
    
    # Configurable interface implementation
    def configure(self, config: Dict[str, Any]) -> None:
        """Apply configuration to this plugin"""
        errors = self.validate_configuration(config)
        if errors:
            raise KumihanError(
                f"Invalid configuration for plugin {self.name}",
                technical_details=f"Validation errors: {[e.message for e in errors]}"
            )
        self._config = config.copy()
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get current plugin configuration"""
        return self._config.copy()
    
    def validate_configuration(self, config: Dict[str, Any]) -> List[KumihanError]:
        """Validate plugin configuration
        
        Default implementation accepts any configuration.
        Override to provide specific validation.
        """
        return []
    
    # Lifecycle interface implementation
    def initialize(self) -> bool:
        """Initialize the plugin"""
        try:
            self._status = "initializing"
            self.enabled = True
            self._status = "initialized"
            return True
        except Exception as e:
            self._status = "error"
            self.enabled = False
            raise KumihanError(
                f"Failed to initialize plugin {self.name}",
                cause=e
            )
    
    def shutdown(self) -> bool:
        """Shutdown the plugin"""
        try:
            self._status = "shutting_down"
            self.enabled = False
            self._status = "shutdown"
            return True
        except Exception as e:
            self._status = "error"
            raise KumihanError(
                f"Failed to shutdown plugin {self.name}",
                cause=e
            )
    
    def is_initialized(self) -> bool:
        """Check if plugin is initialized"""
        return self._status == "initialized"
    
    def get_status(self) -> str:
        """Get current lifecycle status"""
        return self._status


class ParserPlugin(KumihanPlugin):
    """Interface for parser plugins
    
    Parser plugins extend the system's ability to parse different input formats.
    """
    
    @abstractmethod
    def create_parser(self) -> BaseParser:
        """Create a parser instance
        
        Returns:
            BaseParser: Parser instance that handles this plugin's formats
        """
        pass
    
    @abstractmethod
    def get_parser_priority(self) -> int:
        """Get parser priority for format conflicts
        
        Returns:
            int: Priority level (higher = more priority)
        """
        pass


class RendererPlugin(KumihanPlugin):
    """Interface for renderer plugins
    
    Renderer plugins add new output formats to the system.
    """
    
    @abstractmethod
    def create_renderer(self) -> BaseRenderer:
        """Create a renderer instance
        
        Returns:
            BaseRenderer: Renderer instance for this plugin's output format
        """
        pass
    
    @abstractmethod
    def get_output_format(self) -> str:
        """Get output format identifier
        
        Returns:
            str: Format identifier (e.g., 'pdf', 'epub', 'docx')
        """
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension for this format
        
        Returns:
            str: File extension (e.g., '.pdf', '.epub')
        """
        pass


class ValidatorPlugin(KumihanPlugin):
    """Interface for validator plugins
    
    Validator plugins add new validation capabilities.
    """
    
    @abstractmethod
    def create_validator(self) -> BaseValidator:
        """Create a validator instance
        
        Returns:
            BaseValidator: Validator instance for this plugin's validation rules
        """
        pass
    
    @abstractmethod
    def get_validation_scope(self) -> str:
        """Get validation scope
        
        Returns:
            str: Scope identifier (e.g., 'syntax', 'structure', 'style')
        """
        pass


class ProcessorPlugin(KumihanPlugin):
    """Interface for processor plugins
    
    Processor plugins add data transformation capabilities.
    """
    
    @abstractmethod
    def create_processor(self) -> BaseProcessor:
        """Create a processor instance
        
        Returns:
            BaseProcessor: Processor instance for this plugin's transformations
        """
        pass
    
    @abstractmethod
    def get_input_types(self) -> List[Type]:
        """Get supported input types
        
        Returns:
            List[Type]: List of Python types this processor can handle
        """
        pass
    
    @abstractmethod
    def get_output_type(self) -> Type:
        """Get output type
        
        Returns:
            Type: Python type this processor produces
        """
        pass


class PluginMetadata:
    """Metadata container for plugin discovery"""
    
    def __init__(
        self,
        name: str,
        version: str,
        plugin_class: Type[KumihanPlugin],
        file_path: Path,
        enabled: bool = True
    ):
        """Initialize plugin metadata
        
        Args:
            name: Plugin name
            version: Plugin version
            plugin_class: Plugin class type
            file_path: Path to plugin file
            enabled: Whether plugin is enabled
        """
        self.name = name
        self.version = version
        self.plugin_class = plugin_class
        self.file_path = file_path
        self.enabled = enabled
        self.loaded = False
        self.instance: Optional[KumihanPlugin] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'version': self.version,
            'class_name': self.plugin_class.__name__,
            'file_path': str(self.file_path),
            'enabled': self.enabled,
            'loaded': self.loaded,
            'has_instance': self.instance is not None
        }