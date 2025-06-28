"""DIコンテナのインターフェース定義"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Dict, Optional, Type, TypeVar

T = TypeVar("T")


class ServiceLifetime(Enum):
    """サービスのライフタイム定義"""

    SINGLETON = "singleton"  # アプリケーション全体で1つのインスタンス
    TRANSIENT = "transient"  # 要求ごとに新しいインスタンス
    SCOPED = "scoped"  # スコープ内で1つのインスタンス


class ServiceProvider(ABC):
    """サービスプロバイダーの抽象基底クラス"""

    @abstractmethod
    def get_service(self, service_type: Type[T]) -> T:
        """サービスを取得"""
        pass

    @abstractmethod
    def get_service_or_none(self, service_type: Type[T]) -> Optional[T]:
        """サービスを取得（存在しない場合はNone）"""
        pass

    @abstractmethod
    def has_service(self, service_type: Type[T]) -> bool:
        """サービスが登録されているか確認"""
        pass

    @abstractmethod
    def create_scope(self) -> "ServiceScope":
        """新しいスコープを作成"""
        pass


class ServiceScope(ServiceProvider):
    """サービススコープのインターフェース"""

    @abstractmethod
    def dispose(self) -> None:
        """スコープ内のリソースを破棄"""
        pass

    @abstractmethod
    def __enter__(self) -> "ServiceScope":
        """コンテキストマネージャーの開始"""
        pass

    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """コンテキストマネージャーの終了"""
        pass


class ServiceFactory(ABC):
    """サービスファクトリーの抽象基底クラス"""

    @abstractmethod
    def create(self, provider: ServiceProvider) -> Any:
        """サービスインスタンスを作成"""
        pass


class ServiceDescriptor:
    """サービス記述子"""

    def __init__(
        self,
        service_type: Type,
        implementation_type: Optional[Type] = None,
        factory: Optional[Callable[[ServiceProvider], Any]] = None,
        instance: Optional[Any] = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ):
        self.service_type = service_type
        self.implementation_type = implementation_type or service_type
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime

        # バリデーション
        if instance is None and factory is None:
            if not hasattr(self.implementation_type, "__init__"):
                raise ValueError(f"Implementation type {self.implementation_type} must have __init__ method")

    def create_instance(self, provider: ServiceProvider) -> Any:
        """インスタンスを作成"""
        if self.instance is not None:
            return self.instance

        if self.factory is not None:
            return self.factory(provider)

        # コンストラクタインジェクションを使用
        return self._create_with_injection(provider)

    def _create_with_injection(self, provider: ServiceProvider) -> Any:
        """依存性注入を使用してインスタンスを作成"""
        import inspect

        # コンストラクタのパラメータを取得
        sig = inspect.signature(self.implementation_type.__init__)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            # 型ヒントから依存性を解決
            if param.annotation != param.empty:
                try:
                    kwargs[param_name] = provider.get_service(param.annotation)
                except Exception:
                    # オプショナルパラメータの場合はデフォルト値を使用
                    if param.default != param.empty:
                        kwargs[param_name] = param.default
                    else:
                        raise

        return self.implementation_type(**kwargs)
