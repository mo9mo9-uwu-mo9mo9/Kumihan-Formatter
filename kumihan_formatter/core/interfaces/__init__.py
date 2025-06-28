"""Interface definitions for Kumihan-Formatter

This package contains abstract base classes and interfaces that define
consistent patterns across the entire architecture.
"""

from .base_interfaces import (
    BaseHandler,
    BaseManager,
    BaseParser,
    BaseProcessor,
    BaseRenderer,
    BaseValidator,
)
from .component_interfaces import (
    Cacheable,
    Configurable,
    Lifecycle,
    Monitorable,
    Pluggable,
    Validatable,
)
from .service_interfaces import (
    CacheService,
    ConfigurationService,
    EventService,
    ValidationService,
)

__all__ = [
    # Base interfaces
    "BaseManager",
    "BaseHandler",
    "BaseProcessor",
    "BaseValidator",
    "BaseRenderer",
    "BaseParser",
    # Service interfaces
    "ConfigurationService",
    "CacheService",
    "ValidationService",
    "EventService",
    # Component interfaces
    "Configurable",
    "Cacheable",
    "Validatable",
    "Lifecycle",
    "Monitorable",
    "Pluggable",
]
