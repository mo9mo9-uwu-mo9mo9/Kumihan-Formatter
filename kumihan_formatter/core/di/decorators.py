"""依存性注入用のデコレータ"""

import functools
import inspect
from typing import Any, Callable, Optional, Type, TypeVar, get_type_hints

from .container import get_default_container
from .interfaces import ServiceLifetime

T = TypeVar("T")


def injectable(cls: Type[T]) -> Type[T]:
    """クラスを注入可能にマークするデコレータ"""
    # メタデータを追加
    setattr(cls, "_injectable", True)
    return cls


def service(service_type: Optional[Type] = None, lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT):
    """サービスとして自動登録するデコレータ"""

    def decorator(cls: Type[T]) -> Type[T]:
        # メタデータを追加
        setattr(cls, "_service_type", service_type or cls)
        setattr(cls, "_service_lifetime", lifetime)
        setattr(cls, "_auto_register", True)

        # デフォルトコンテナに自動登録
        container = get_default_container()
        if lifetime == ServiceLifetime.SINGLETON:
            container.register_singleton(service_type or cls, cls)
        elif lifetime == ServiceLifetime.SCOPED:
            container.register_scoped(service_type or cls, cls)
        else:
            container.register_transient(service_type or cls, cls)

        return cls

    return decorator


def inject(func: Callable[..., T]) -> Callable[..., T]:
    """関数の引数に依存性注入を行うデコレータ"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 関数のシグネチャを取得
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        # コンテナを取得
        container = get_default_container()

        # 引数を解決
        bound_args = sig.bind_partial(*args, **kwargs)

        for param_name, param in sig.parameters.items():
            # 既に値が提供されている場合はスキップ
            if param_name in bound_args.arguments:
                continue

            # 型ヒントから依存性を解決
            if param_name in type_hints:
                param_type = type_hints[param_name]
                try:
                    service = container.get_service(param_type)
                    bound_args.arguments[param_name] = service
                except Exception:
                    # デフォルト値がある場合は使用
                    if param.default != param.empty:
                        bound_args.arguments[param_name] = param.default
                    else:
                        raise

        # 完全な引数で関数を呼び出し
        bound_args.apply_defaults()
        return func(*bound_args.args, **bound_args.kwargs)

    return wrapper


def singleton(service_type: Optional[Type] = None):
    """シングルトンサービスとして登録するデコレータ"""
    return service(service_type, ServiceLifetime.SINGLETON)


def scoped(service_type: Optional[Type] = None):
    """スコープドサービスとして登録するデコレータ"""
    return service(service_type, ServiceLifetime.SCOPED)


def transient(service_type: Optional[Type] = None):
    """トランジェントサービスとして登録するデコレータ"""
    return service(service_type, ServiceLifetime.TRANSIENT)


# 型アノテーション用ヘルパー


class Injected:
    """依存性注入される引数をマークするクラス"""

    def __init__(self, service_type: Type):
        self.service_type = service_type

    def __class_getitem__(cls, service_type: Type):
        return cls(service_type)


def resolve(service_type: Type[T]) -> T:
    """サービスを直接解決する関数"""
    container = get_default_container()
    return container.get_service(service_type)


def resolve_or_none(service_type: Type[T]) -> Optional[T]:
    """サービスを直接解決する関数（存在しない場合はNone）"""
    container = get_default_container()
    return container.get_service_or_none(service_type)
