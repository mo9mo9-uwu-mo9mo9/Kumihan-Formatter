"""依存性注入コンテナモジュール"""

from .container import DIContainer, ServiceLifetime
from .decorators import inject, injectable, service
from .exceptions import (
    CircularDependencyError,
    DIContainerError,
    ServiceNotFoundError,
    ServiceRegistrationError,
)
from .interfaces import ServiceFactory, ServiceProvider

__all__ = [
    # コンテナ
    "DIContainer",
    "ServiceLifetime",
    # デコレータ
    "inject",
    "injectable",
    "service",
    # インターフェース
    "ServiceProvider",
    "ServiceFactory",
    # 例外
    "DIContainerError",
    "ServiceNotFoundError",
    "CircularDependencyError",
    "ServiceRegistrationError",
]
