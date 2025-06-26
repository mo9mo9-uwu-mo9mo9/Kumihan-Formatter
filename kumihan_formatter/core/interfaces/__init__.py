"""Interface definitions for Kumihan-Formatter

This package contains abstract base classes and interfaces that define
consistent patterns across the entire architecture.
"""

from .base_interfaces import (
    BaseManager,
    BaseHandler,
    BaseProcessor,
    BaseValidator,
    BaseRenderer,
    BaseParser
)
from .service_interfaces import (
    ConfigurationService,
    CacheService,
    ValidationService,
    EventService
)
from .component_interfaces import (
    Configurable,
    Cacheable,
    Validatable,
    Lifecycle,
    Monitorable,
    Pluggable
)

__all__ = [
    # Base interfaces
    'BaseManager',
    'BaseHandler', 
    'BaseProcessor',
    'BaseValidator',
    'BaseRenderer',
    'BaseParser',
    
    # Service interfaces
    'ConfigurationService',
    'CacheService',
    'ValidationService',
    'EventService',
    
    # Component interfaces
    'Configurable',
    'Cacheable',
    'Validatable',
    'Lifecycle',
    'Monitorable',
    'Pluggable'
]