"""Decorator Pattern Implementation"""

import inspect
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar

T = TypeVar("T")
P = TypeVar("P")
R = TypeVar("R")


class ParserDecorator(ABC):
    """パーサーデコレーター基底クラス"""

    def __init__(self, wrapped_parser: Any) -> None:
        self._wrapped_parser = wrapped_parser

    @abstractmethod
    def parse(self, content: str, context: Dict[str, Any]) -> Any:
        """デコレート済みパース処理"""
        pass

    def __getattr__(self, name: str) -> Any:
        """委譲処理"""
        return getattr(self._wrapped_parser, name)


class RendererDecorator(ABC):
    """レンダラーデコレーター基底クラス"""

    def __init__(self, wrapped_renderer: Any) -> None:
        self._wrapped_renderer = wrapped_renderer

    @abstractmethod
    def render(self, data: Any, context: Dict[str, Any]) -> str:
        """デコレート済みレンダリング処理"""
        pass

    def __getattr__(self, name: str) -> Any:
        """委譲処理"""
        return getattr(self._wrapped_renderer, name)


class CachingParserDecorator(ParserDecorator):
    """キャッシュ機能付きパーサーデコレーター"""

    def __init__(self, wrapped_parser: Any, cache_size: int = 128) -> None:
        super().__init__(wrapped_parser)
        self._cache: Dict[str, Any] = {}
        self._cache_size = cache_size
        self._access_order: List[str] = []

    def parse(self, content: str, context: Dict[str, Any]) -> Any:
        """キャッシュ付きパース処理"""
        cache_key = self._generate_cache_key(content, context)

        if cache_key in self._cache:
            # キャッシュヒット
            self._update_access_order(cache_key)
            return self._cache[cache_key]

        # パース実行
        result = self._wrapped_parser.parse(content, context)

        # キャッシュ保存
        self._store_in_cache(cache_key, result)

        return result

    def _generate_cache_key(self, content: str, context: Dict[str, Any]) -> str:
        """キャッシュキー生成"""
        import hashlib

        content_hash = hashlib.md5(content.encode()).hexdigest()
        context_str = str(sorted(context.items()))
        context_hash = hashlib.md5(context_str.encode()).hexdigest()
        return f"{content_hash}:{context_hash}"

    def _store_in_cache(self, key: str, value: Any) -> None:
        """キャッシュ保存"""
        if len(self._cache) >= self._cache_size and key not in self._cache:
            # LRU削除
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]

        self._cache[key] = value
        self._update_access_order(key)

    def _update_access_order(self, key: str) -> None:
        """アクセス順序更新"""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)


class LoggingDecorator(Generic[T]):
    """ログ機能デコレーター"""

    def __init__(self, wrapped_object: T, logger_name: str = "decorator") -> None:
        self._wrapped_object = wrapped_object
        self._logger_name = logger_name

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._wrapped_object, name)
        if callable(attr):

            @wraps(attr)
            def logged_method(*args: Any, **kwargs: Any) -> Any:
                # メソッド呼び出しログ
                self._log_method_call(name, args, kwargs)
                try:
                    result = attr(*args, **kwargs)
                    self._log_method_success(name, result)
                    return result
                except Exception as e:
                    self._log_method_error(name, e)
                    raise

            return logged_method
        return attr

    def _log_method_call(
        self, method_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> None:
        """メソッド呼び出しログ"""
        pass  # 実際のログ実装

    def _log_method_success(self, method_name: str, result: Any) -> None:
        """メソッド成功ログ"""
        pass  # 実際のログ実装

    def _log_method_error(self, method_name: str, error: Exception) -> None:
        """メソッドエラーログ"""
        pass  # 実際のログ実装


class DecoratorChain:
    """デコレーターチェーン管理"""

    def __init__(self, base_object: Any) -> None:
        self._base_object = base_object
        self._decorators: List[Callable[[Any], Any]] = []

    def add_decorator(
        self, decorator_factory: Callable[[Any], Any]
    ) -> "DecoratorChain":
        """デコレーター追加"""
        self._decorators.append(decorator_factory)
        return self

    def build(self) -> Any:
        """デコレートされたオブジェクト構築"""
        result = self._base_object
        for decorator_factory in self._decorators:
            result = decorator_factory(result)
        return result


# 便利なデコレーター関数
def with_caching(
    cache_size: int = 128,
) -> Callable[[Type[T]], Callable[..., CachingParserDecorator]]:
    """キャッシュデコレーター関数"""

    def decorator(parser_class: Type[T]) -> Callable[..., CachingParserDecorator]:
        def create_cached_parser(*args: Any, **kwargs: Any) -> CachingParserDecorator:
            instance = parser_class(*args, **kwargs)
            return CachingParserDecorator(instance, cache_size)

        return create_cached_parser

    return decorator


def with_logging(
    logger_name: str = "default",
) -> Callable[[Type[T]], Callable[..., LoggingDecorator[T]]]:
    """ログデコレーター関数"""

    def decorator(target_class: Type[T]) -> Callable[..., LoggingDecorator[T]]:
        def create_logged_instance(*args: Any, **kwargs: Any) -> LoggingDecorator[T]:
            instance = target_class(*args, **kwargs)
            return LoggingDecorator(instance, logger_name)

        return create_logged_instance

    return decorator
