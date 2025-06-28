"""DIコンテナ関連の例外定義"""

from typing import List, Optional


class DIContainerError(Exception):
    """DIコンテナの基底例外クラス"""

    pass


class ServiceNotFoundError(DIContainerError):
    """サービスが見つからない場合の例外"""

    def __init__(self, service_type: type, message: Optional[str] = None):
        self.service_type = service_type
        if message is None:
            message = f"Service of type '{service_type.__name__}' is not registered"
        super().__init__(message)


class CircularDependencyError(DIContainerError):
    """循環依存が検出された場合の例外"""

    def __init__(self, dependency_chain: List[type]):
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join(t.__name__ for t in dependency_chain)
        message = f"Circular dependency detected: {chain_str}"
        super().__init__(message)


class ServiceRegistrationError(DIContainerError):
    """サービス登録エラー"""

    def __init__(self, service_type: type, message: str):
        self.service_type = service_type
        full_message = f"Failed to register service '{service_type.__name__}': {message}"
        super().__init__(full_message)


class ServiceResolutionError(DIContainerError):
    """サービス解決エラー"""

    def __init__(self, service_type: type, message: str):
        self.service_type = service_type
        full_message = f"Failed to resolve service '{service_type.__name__}': {message}"
        super().__init__(full_message)
