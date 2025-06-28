"""Component interfaces for consistent behavior patterns

This module defines mixin interfaces that components can implement
to provide consistent behavior patterns across the system.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..common import KumihanError


class Configurable(ABC):
    """Interface for components that can be configured

    Components implementing this interface can receive and apply configuration.
    """

    @abstractmethod
    def configure(self, config: Dict[str, Any]) -> None:
        """Apply configuration to this component

        Args:
            config: Configuration dictionary

        Raises:
            KumihanError: If configuration is invalid
        """
        pass

    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration

        Returns:
            Dict[str, Any]: Current configuration
        """
        pass

    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> List[KumihanError]:
        """Validate configuration without applying it

        Args:
            config: Configuration to validate

        Returns:
            List[KumihanError]: Validation errors (empty if valid)
        """
        pass


class Cacheable(ABC):
    """Interface for components that support caching

    Components implementing this interface can cache their results.
    """

    @abstractmethod
    def get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key for given parameters

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            str: Cache key
        """
        pass

    @abstractmethod
    def should_cache(self, *args, **kwargs) -> bool:
        """Determine if result should be cached

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            bool: True if should cache
        """
        pass

    @abstractmethod
    def get_cache_ttl(self, *args, **kwargs) -> Optional[int]:
        """Get time-to-live for cache entry

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Optional[int]: TTL in seconds, None for default
        """
        pass


class Validatable(ABC):
    """Interface for components that can validate themselves

    Components implementing this interface can perform self-validation.
    """

    @abstractmethod
    def validate_self(self) -> List[KumihanError]:
        """Validate this component's current state

        Returns:
            List[KumihanError]: Validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        """Check if this component is in a valid state

        Returns:
            bool: True if valid
        """
        pass

    @abstractmethod
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary

        Returns:
            Dict[str, Any]: Validation summary with error counts, etc.
        """
        pass


class Lifecycle(ABC):
    """Interface for components with lifecycle management

    Components implementing this interface support initialization and cleanup.
    """

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize this component

        Returns:
            bool: True if initialization successful

        Raises:
            KumihanError: If initialization fails
        """
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Shutdown and cleanup this component

        Returns:
            bool: True if shutdown successful

        Raises:
            KumihanError: If shutdown fails
        """
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if component is initialized

        Returns:
            bool: True if initialized
        """
        pass

    @abstractmethod
    def get_status(self) -> str:
        """Get current lifecycle status

        Returns:
            str: Status ('uninitialized', 'initializing', 'initialized', 'shutting_down', 'shutdown')
        """
        pass


class Monitorable(ABC):
    """Interface for components that provide monitoring data

    Components implementing this interface can report metrics and health status.
    """

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get component metrics

        Returns:
            Dict[str, Any]: Component metrics
        """
        pass

    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Get component health status

        Returns:
            Dict[str, Any]: Health status with status code and details
        """
        pass

    @abstractmethod
    def reset_metrics(self) -> None:
        """Reset component metrics"""
        pass


class Pluggable(ABC):
    """Interface for components that support plugins

    Components implementing this interface can load and manage plugins.
    """

    @abstractmethod
    def load_plugin(self, plugin_path: Path) -> bool:
        """Load a plugin

        Args:
            plugin_path: Path to plugin file or directory

        Returns:
            bool: True if loaded successfully

        Raises:
            KumihanError: If plugin loading fails
        """
        pass

    @abstractmethod
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin

        Args:
            plugin_name: Name of plugin to unload

        Returns:
            bool: True if unloaded successfully
        """
        pass

    @abstractmethod
    def get_loaded_plugins(self) -> List[str]:
        """Get list of loaded plugins

        Returns:
            List[str]: Plugin names
        """
        pass

    @abstractmethod
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get plugin information

        Args:
            plugin_name: Name of plugin

        Returns:
            Optional[Dict[str, Any]]: Plugin info or None if not found
        """
        pass
