"""依存関係注入（DI）コンテナ実装

Issue #914: アーキテクチャ最適化
2025年Pythonベストプラクティス準拠のDIシステム
"""

import inspect
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

from ..utilities.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class ServiceLifetime(Enum):
    """サービスのライフタイム管理"""

    SINGLETON = "singleton"  # アプリケーション全体で1インスタンス
    SCOPED = "scoped"  # スコープごとに1インスタンス
    TRANSIENT = "transient"  # 要求ごとに新規インスタンス


@dataclass
class ServiceDescriptor:
    """サービス記述子"""

    interface: Type[Any]
    implementation: Union[Type[Any], Callable[..., Any], Any]
    lifetime: ServiceLifetime
    factory: Optional[Callable[["DIContainer"], Any]] = None


class CircularDependencyError(Exception):
    """循環参照エラー"""

    pass


class ServiceNotFoundError(Exception):
    """サービス未登録エラー"""

    pass


class DIContainer:
    """依存関係注入コンテナ

    機能:
    - サービス登録・解決
    - ライフタイム管理
    - 自動依存関係解決
    - 循環参照検出
    """

    def __init__(self) -> None:
        self._services: Dict[Type[Any], ServiceDescriptor] = {}
        self._singletons: Dict[Type[Any], Any] = {}
        self._resolving: List[Type[Any]] = []  # 循環参照検出用

    def register(
        self,
        interface: Type[T],
        implementation: Union[Type[T], Callable[[], T], T],
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON,
    ) -> None:
        """サービス登録"""
        try:
            descriptor = ServiceDescriptor(
                interface=interface, implementation=implementation, lifetime=lifetime
            )
            self._services[interface] = descriptor
            logger.debug(
                f"Service registered: {interface.__name__} -> {implementation}"
            )
        except Exception as e:
            logger.error(
                f"Service registration failed: {interface.__name__}, error: {e}"
            )
            raise

    def register_singleton(self, interface: Type[T], instance: T) -> None:
        """シングルトンインスタンス直接登録"""
        try:
            self._singletons[interface] = instance
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=instance,
                lifetime=ServiceLifetime.SINGLETON,
            )
            self._services[interface] = descriptor
            logger.debug(f"Singleton registered: {interface.__name__}")
        except Exception as e:
            logger.error(
                f"Singleton registration failed: {interface.__name__}, error: {e}"
            )
            raise

    def register_factory(
        self,
        interface: Type[T],
        factory: Callable[["DIContainer"], T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> None:
        """ファクトリー関数登録"""
        try:
            descriptor = ServiceDescriptor(
                interface=interface,
                implementation=factory,
                lifetime=lifetime,
                factory=factory,
            )
            self._services[interface] = descriptor
            logger.debug(f"Factory registered: {interface.__name__}")
        except Exception as e:
            logger.error(
                f"Factory registration failed: {interface.__name__}, error: {e}"
            )
            raise

    def resolve(self, interface: Type[T]) -> T:
        """サービス解決"""
        try:
            # 循環参照チェック
            if self._detect_circular_dependency(interface):
                raise CircularDependencyError(
                    f"Circular dependency detected for {interface.__name__}"
                )

            # ServiceDescriptor取得
            if interface not in self._services:
                raise ServiceNotFoundError(
                    f"Service not registered: {interface.__name__}"
                )

            descriptor = self._services[interface]

            # ライフタイムに応じたインスタンス生成/取得
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                if interface in self._singletons:
                    return cast(T, self._singletons[interface])

                self._resolving.append(interface)
                try:
                    if descriptor.factory:
                        instance = descriptor.factory(self)
                    else:
                        instance = self._create_instance(descriptor.implementation)
                    self._singletons[interface] = instance
                    return cast(T, instance)
                finally:
                    self._resolving.remove(interface)

            elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
                self._resolving.append(interface)
                try:
                    if descriptor.factory:
                        return cast(T, descriptor.factory(self))
                    else:
                        return cast(T, self._create_instance(descriptor.implementation))
                finally:
                    self._resolving.remove(interface)

            else:  # SCOPED - デフォルトでTRANSIENTと同じ動作
                self._resolving.append(interface)
                try:
                    if descriptor.factory:
                        return cast(T, descriptor.factory(self))
                    else:
                        return cast(T, self._create_instance(descriptor.implementation))
                finally:
                    self._resolving.remove(interface)

        except Exception as e:
            logger.error(f"Service resolution failed: {interface.__name__}, error: {e}")
            raise

    def create_scope(self) -> "ServiceScope":
        """新規スコープ作成"""
        return ServiceScope(self)

    def _create_instance(self, service_type: Union[Type[T], Any]) -> T:
        """インスタンス生成と依存関係注入"""
        try:
            # インスタンスがすでに生成済みの場合は返す
            if not inspect.isclass(service_type):
                return cast(T, service_type)

            # コンストラクタ引数取得
            init_signature = inspect.signature(service_type.__init__)
            parameters = list(init_signature.parameters.values())[1:]  # selfを除く

            # 依存関係解決
            kwargs = {}
            for param in parameters:
                if param.annotation == inspect.Parameter.empty:
                    continue

                # 型注釈から依存関係を解決
                param_type = param.annotation
                if param_type in self._services:
                    kwargs[param.name] = self.resolve(param_type)
                elif param.default != inspect.Parameter.empty:
                    # デフォルト値がある場合はスキップ
                    continue
                else:
                    logger.warning(
                        f"Dependency not found for {param.name}: {param_type}"
                    )

            # インスタンス生成
            return cast(T, service_type(**kwargs))

        except Exception as e:
            logger.error(f"Instance creation failed: {service_type}, error: {e}")
            raise

    def _detect_circular_dependency(self, service_type: Type[Any]) -> bool:
        """循環参照検出"""
        return service_type in self._resolving


class ServiceScope:
    """DIスコープ - スコープ付きサービス管理"""

    def __init__(self, container: DIContainer) -> None:
        self.container = container
        self._scoped_instances: Dict[Type, Any] = {}

    def resolve(self, interface: Type[T]) -> T:
        """スコープ内でサービス解決"""
        try:
            if interface not in self.container._services:
                raise ServiceNotFoundError(
                    f"Service not registered: {interface.__name__}"
                )

            descriptor = self.container._services[interface]

            if descriptor.lifetime == ServiceLifetime.SCOPED:
                if interface in self._scoped_instances:
                    return cast(T, self._scoped_instances[interface])

                instance = self.container.resolve(interface)
                self._scoped_instances[interface] = instance
                return instance
            else:
                return self.container.resolve(interface)

        except Exception as e:
            logger.error(
                f"Scoped service resolution failed: {interface.__name__}, error: {e}"
            )
            raise


# デコレーター
def injectable(cls: Type[T]) -> Type[T]:
    """クラスをDI対応にするデコレーター"""
    original_init = cls.__init__

    @wraps(original_init)
    def new_init(self: Any, *args: Any, **kwargs: Any) -> None:
        # 依存関係自動注入ロジック
        try:
            container = get_container()

            # 型注釈から依存関係を取得
            init_signature = inspect.signature(original_init)
            parameters = list(init_signature.parameters.values())[1:]  # selfを除く

            # 未提供の引数について依存関係解決を試行
            for param in parameters:
                if (
                    param.name not in kwargs
                    and param.annotation != inspect.Parameter.empty
                ):
                    param_type = param.annotation
                    if param_type in container._services:
                        kwargs[param.name] = container.resolve(param_type)

            original_init(self, *args, **kwargs)

        except Exception as e:
            logger.warning(f"DI injection failed for {cls.__name__}: {e}")
            original_init(self, *args, **kwargs)

    setattr(cls, "__init__", new_init)
    return cls


def inject(**dependencies: Type[Any]) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """依存関係を明示的に指定するデコレーター"""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                container = get_container()

                # 依存関係注入
                for name, service_type in dependencies.items():
                    if name not in kwargs:
                        kwargs[name] = container.resolve(service_type)

                return func(*args, **kwargs)

            except Exception as e:
                logger.warning(f"DI injection failed for {func.__name__}: {e}")
                return func(*args, **kwargs)

        return wrapper

    return decorator


# グローバルコンテナインスタンス
_global_container = DIContainer()


def get_container() -> DIContainer:
    """グローバルコンテナ取得"""
    return _global_container


def register_services(container: DIContainer) -> None:
    """標準サービス登録"""
    try:
        # 基本プロトコルのインポートを試行

        logger.info("Standard services registration completed")

    except ImportError as e:
        logger.warning(f"Could not import some protocols for service registration: {e}")
    except Exception as e:
        logger.error(f"Service registration failed: {e}")
        raise
