"""GUI Debug Logger Decorators for Kumihan-Formatter
開発用デバッグロガーのデコレータ機能
"""

import functools
import time
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from .debug_logger_core import GUIDebugLogger


def log_gui_method(
    logger_instance: "GUIDebugLogger",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """GUIメソッド用デコレータ"""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # ログ無効時はオーバーヘッドを最小化
            if not logger_instance.enabled:
                return func(*args, **kwargs)
            func_name = f"{args[0].__class__.__name__}.{func.__name__}"
            logger_instance.log_function_call(func_name, args[1:], kwargs)
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger_instance.log_performance(func_name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger_instance.error(f"Error in {func_name} after {duration:.3f}s", e)
                raise

        return wrapper

    return decorator


def log_import_attempt(
    module_name: str, logger_instance: "GUIDebugLogger"
) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
    """インポート試行をログ"""

    def decorator(import_func: Callable[[], Any]) -> Callable[[], Any]:
        @functools.wraps(import_func)
        def wrapper() -> Any:
            # ログ無効時はオーバーヘッドを最小化
            if not logger_instance.enabled:
                return import_func()
            logger_instance.debug(f"Attempting to import: {module_name}")
            try:
                result = import_func()
                logger_instance.info(f"Successfully imported: {module_name}")
                return result
            except Exception as e:
                logger_instance.error(f"Failed to import {module_name}", e)
                raise

        return wrapper

    return decorator


def create_gui_method_decorator(
    logger_instance: "GUIDebugLogger",
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """グローバルロガーを使用するGUIメソッドデコレータを作成"""
    return log_gui_method(logger_instance)
