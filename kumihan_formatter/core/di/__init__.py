"""依存性注入コンテナモジュール"""

from .container import DIContainer, ServiceLifetime
from .decorators import inject, injectable, service
from .interfaces import ServiceProvider, ServiceFactory
from .exceptions import (
    DIContainerError,
    ServiceNotFoundError,
    CircularDependencyError,
    ServiceRegistrationError
)

__all__ = [
    # コンテナ
    'DIContainer',
    'ServiceLifetime',
    
    # デコレータ
    'inject',
    'injectable',
    'service',
    
    # インターフェース
    'ServiceProvider',
    'ServiceFactory',
    
    # 例外
    'DIContainerError',
    'ServiceNotFoundError',
    'CircularDependencyError',
    'ServiceRegistrationError',
]