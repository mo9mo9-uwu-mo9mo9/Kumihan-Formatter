"""依存性注入コンテナの実装"""

import threading
import weakref
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, Optional, Set, Type, TypeVar, Union

from .exceptions import (
    CircularDependencyError,
    ServiceNotFoundError,
    ServiceRegistrationError,
    ServiceResolutionError,
)
from .interfaces import (
    ServiceDescriptor,
    ServiceFactory,
    ServiceLifetime,
    ServiceProvider,
    ServiceScope,
)

T = TypeVar("T")


class DIContainer(ServiceProvider):
    """依存性注入コンテナの実装クラス"""

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._resolution_stack: Set[Type] = set()

    # サービス登録メソッド

    def register_singleton(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[ServiceProvider], T]] = None,
        instance: Optional[T] = None,
    ) -> "DIContainer":
        """シングルトンサービスを登録"""
        return self._register(service_type, implementation_type, factory, instance, ServiceLifetime.SINGLETON)

    def register_transient(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[ServiceProvider], T]] = None,
    ) -> "DIContainer":
        """トランジェントサービスを登録"""
        return self._register(service_type, implementation_type, factory, None, ServiceLifetime.TRANSIENT)

    def register_scoped(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]] = None,
        factory: Optional[Callable[[ServiceProvider], T]] = None,
    ) -> "DIContainer":
        """スコープドサービスを登録"""
        return self._register(service_type, implementation_type, factory, None, ServiceLifetime.SCOPED)

    def _register(
        self,
        service_type: Type[T],
        implementation_type: Optional[Type[T]],
        factory: Optional[Callable[[ServiceProvider], T]],
        instance: Optional[T],
        lifetime: ServiceLifetime,
    ) -> "DIContainer":
        """サービスを登録（内部メソッド）"""
        with self._lock:
            try:
                descriptor = ServiceDescriptor(
                    service_type=service_type,
                    implementation_type=implementation_type,
                    factory=factory,
                    instance=instance,
                    lifetime=lifetime,
                )
                self._services[service_type] = descriptor

                # インスタンスが提供されている場合はシングルトンとして保存
                if instance is not None:
                    self._singletons[service_type] = instance

            except Exception as e:
                raise ServiceRegistrationError(service_type, str(e))

        return self

    # サービス取得メソッド

    def get_service(self, service_type: Type[T]) -> T:
        """サービスを取得"""
        service = self.get_service_or_none(service_type)
        if service is None:
            raise ServiceNotFoundError(service_type)
        return service

    def get_service_or_none(self, service_type: Type[T]) -> Optional[T]:
        """サービスを取得（存在しない場合はNone）"""
        with self._lock:
            if service_type not in self._services:
                return None

            descriptor = self._services[service_type]

            # 循環依存チェック
            if service_type in self._resolution_stack:
                chain = list(self._resolution_stack)
                chain.append(service_type)
                raise CircularDependencyError(chain)

            self._resolution_stack.add(service_type)
            try:
                return self._resolve_service(descriptor)
            finally:
                self._resolution_stack.remove(service_type)

    def _resolve_service(self, descriptor: ServiceDescriptor) -> Any:
        """サービスを解決（内部メソッド）"""
        # シングルトンの場合
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if descriptor.service_type in self._singletons:
                return self._singletons[descriptor.service_type]

            # 新規作成
            instance = descriptor.create_instance(self)
            self._singletons[descriptor.service_type] = instance
            return instance

        # トランジェントの場合
        elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
            return descriptor.create_instance(self)

        # スコープドの場合（ルートコンテナではトランジェントと同じ）
        else:
            return descriptor.create_instance(self)

    def has_service(self, service_type: Type[T]) -> bool:
        """サービスが登録されているか確認"""
        return service_type in self._services

    # スコープ管理

    def create_scope(self) -> "ServiceScope":
        """新しいスコープを作成"""
        return DIScope(self)

    # ユーティリティメソッド

    def get_all_services(self, service_type: Type[T]) -> List[T]:
        """指定された型の全てのサービスを取得"""
        services = []
        for svc_type, descriptor in self._services.items():
            if issubclass(descriptor.implementation_type, service_type):
                services.append(self.get_service(svc_type))
        return services

    def clear(self) -> None:
        """全てのサービスをクリア"""
        with self._lock:
            self._services.clear()
            self._singletons.clear()
            self._resolution_stack.clear()


class DIScope(ServiceScope):
    """DIコンテナのスコープ実装"""

    def __init__(self, parent: DIContainer):
        self._parent = parent
        self._scoped_instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
        self._disposed = False

    def get_service(self, service_type: Type[T]) -> T:
        """サービスを取得"""
        if self._disposed:
            raise ServiceResolutionError(service_type, "Scope has been disposed")

        service = self.get_service_or_none(service_type)
        if service is None:
            raise ServiceNotFoundError(service_type)
        return service

    def get_service_or_none(self, service_type: Type[T]) -> Optional[T]:
        """サービスを取得（存在しない場合はNone）"""
        if self._disposed:
            return None

        with self._lock:
            # 親コンテナにサービスが登録されているか確認
            if not self._parent.has_service(service_type):
                return None

            descriptor = self._parent._services[service_type]

            # スコープドサービスの場合
            if descriptor.lifetime == ServiceLifetime.SCOPED:
                if service_type in self._scoped_instances:
                    return self._scoped_instances[service_type]

                # 新規作成
                instance = descriptor.create_instance(self)
                self._scoped_instances[service_type] = instance
                return instance

            # その他のライフタイムは親に委譲
            return self._parent.get_service_or_none(service_type)

    def has_service(self, service_type: Type[T]) -> bool:
        """サービスが登録されているか確認"""
        return self._parent.has_service(service_type)

    def create_scope(self) -> "ServiceScope":
        """新しいスコープを作成（ネストされたスコープ）"""
        return DIScope(self._parent)

    def dispose(self) -> None:
        """スコープ内のリソースを破棄"""
        if self._disposed:
            return

        with self._lock:
            # IDisposableを実装しているインスタンスを破棄
            for instance in self._scoped_instances.values():
                if hasattr(instance, "dispose") and callable(instance.dispose):
                    try:
                        instance.dispose()
                    except Exception:
                        pass  # エラーは無視

            self._scoped_instances.clear()
            self._disposed = True

    def __enter__(self) -> "DIScope":
        """コンテキストマネージャーの開始"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """コンテキストマネージャーの終了"""
        self.dispose()


# グローバルコンテナインスタンス
_default_container: Optional[DIContainer] = None
_container_lock = threading.Lock()


def get_default_container() -> DIContainer:
    """デフォルトコンテナを取得"""
    global _default_container

    if _default_container is None:
        with _container_lock:
            if _default_container is None:
                _default_container = DIContainer()

    return _default_container


def set_default_container(container: DIContainer) -> None:
    """デフォルトコンテナを設定"""
    global _default_container
    with _container_lock:
        _default_container = container
