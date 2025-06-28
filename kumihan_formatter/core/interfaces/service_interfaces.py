"""Service interfaces for dependency injection and architecture

This module defines service interfaces that support dependency injection
and provide clear contracts for core system services.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from ..common import KumihanError


class ConfigurationService(ABC):
    """Interface for configuration management services

    Provides centralized access to configuration data across the system.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        pass

    @abstractmethod
    def load_from_file(self, file_path: Path) -> bool:
        """Load configuration from file

        Args:
            file_path: Path to configuration file

        Returns:
            bool: True if loaded successfully
        """
        pass

    @abstractmethod
    def validate_configuration(self) -> List[KumihanError]:
        """Validate current configuration

        Returns:
            List[KumihanError]: Validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary

        Returns:
            Dict[str, Any]: All configuration values
        """
        pass


class CacheService(ABC):
    """Interface for caching services

    Provides unified caching capabilities across the system.
    """

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get cached value

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set cached value

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        pass

    @abstractmethod
    def remove(self, key: str) -> bool:
        """Remove cached value

        Args:
            key: Cache key to remove

        Returns:
            bool: True if removed, False if not found
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all cached values"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics

        Returns:
            Dict[str, Any]: Cache statistics
        """
        pass


class ValidationService(ABC):
    """Interface for validation services

    Provides centralized validation capabilities.
    """

    @abstractmethod
    def validate(self, data: Any, schema: str) -> List[KumihanError]:
        """Validate data against schema

        Args:
            data: Data to validate
            schema: Schema identifier or definition

        Returns:
            List[KumihanError]: Validation errors (empty if valid)
        """
        pass

    @abstractmethod
    def is_valid(self, data: Any, schema: str) -> bool:
        """Check if data is valid

        Args:
            data: Data to validate
            schema: Schema identifier

        Returns:
            bool: True if valid
        """
        pass

    @abstractmethod
    def register_schema(self, name: str, schema: Dict[str, Any]) -> None:
        """Register a validation schema

        Args:
            name: Schema name
            schema: Schema definition
        """
        pass

    @abstractmethod
    def get_available_schemas(self) -> List[str]:
        """Get list of available schemas

        Returns:
            List[str]: Schema names
        """
        pass


class EventService(ABC):
    """Interface for event handling services

    Provides event-driven architecture support.
    """

    @abstractmethod
    def emit(self, event_name: str, data: Any = None) -> None:
        """Emit an event

        Args:
            event_name: Name of the event
            data: Optional event data
        """
        pass

    @abstractmethod
    def subscribe(self, event_name: str, handler: Callable[[Any], None]) -> str:
        """Subscribe to an event

        Args:
            event_name: Name of the event
            handler: Event handler function

        Returns:
            str: Subscription ID
        """
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from an event

        Args:
            subscription_id: Subscription ID from subscribe()

        Returns:
            bool: True if unsubscribed successfully
        """
        pass

    @abstractmethod
    def get_event_stats(self) -> Dict[str, Any]:
        """Get event statistics

        Returns:
            Dict[str, Any]: Event statistics
        """
        pass
