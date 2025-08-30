"""
OptimizationManager - 最適化機能統合管理クラス
パフォーマンス最適化・メモリ管理・処理効率化の統合
"""

import logging
import time
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass
from functools import wraps

from kumihan_formatter.core.ast_nodes.node import Node


@dataclass
class PerformanceMetrics:
    """パフォーマンス測定結果"""

    operation_name: str
    execution_time: float
    memory_usage: int
    input_size: int
    optimization_applied: bool


class OptimizationManager:
    """最適化機能統合管理クラス - パフォーマンス・メモリ・処理効率の統合API"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        OptimizationManager初期化

        Args:
            config: 設定オプション辞書
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}

        # 最適化設定
        self.enable_caching = self.config.get("enable_caching", True)
        self.enable_parallel = self.config.get("enable_parallel", True)
        self.memory_limit = self.config.get("memory_limit_mb", 512)
        self.performance_monitoring = self.config.get("performance_monitoring", True)

        # パフォーマンス測定
        self._metrics: List[PerformanceMetrics] = []
        self._operation_cache: Dict[str, Any] = {}

    # ========== パフォーマンス最適化 ==========

    def optimize_parsing(
        self, content: Union[str, List[str]], parser_func: Callable[[str], Any]
    ) -> Any:
        """
        パーシング処理の最適化

        Args:
            content: 解析対象コンテンツ
            parser_func: パーサー関数

        Returns:
            最適化された解析結果
        """
        try:
            start_time = time.time()

            # コンテンツサイズチェック
            if isinstance(content, str):
                input_size = len(content)
                content_hash = hash(content)
            else:
                input_size = sum(len(line) for line in content)
                content_hash = hash(str(content))

            # キャッシュチェック
            cache_key = f"parse_{content_hash}_{parser_func.__name__}"
            if self.enable_caching and cache_key in self._operation_cache:
                self.logger.debug(f"キャッシュヒット: {parser_func.__name__}")
                cached_result = self._operation_cache[cache_key]

                # メトリクス記録
                execution_time = time.time() - start_time
                self._record_metrics(
                    "parse_cached", execution_time, 0, input_size, True
                )

                return cached_result

            # 最適化されたパーシング実行
            if input_size > 50000:  # 大きなコンテンツの場合
                result = self._optimize_large_parsing(content, parser_func)
            else:
                result = parser_func(content)

            # キャッシュ保存
            if self.enable_caching:
                self._operation_cache[cache_key] = result

            # メトリクス記録
            execution_time = time.time() - start_time
            self._record_metrics(
                parser_func.__name__,
                execution_time,
                self._estimate_memory_usage(result),
                input_size,
                True,
            )

            return result

        except Exception as e:
            self.logger.error(f"パーシング最適化中にエラー: {e}")
            # フォールバック: 通常のパーシング
            return parser_func(content)

    def _optimize_large_parsing(
        self, content: Union[str, List[str]], parser_func: Callable[[str], Any]
    ) -> Any:
        """大きなコンテンツの最適化パーシング"""
        try:
            if isinstance(content, str):
                lines = content.split("\n")
            else:
                lines = content

            # チャンク分割による並列処理（簡易版）
            chunk_size = self.config.get("large_parse_chunk_size", 1000)
            chunks = [
                lines[i : i + chunk_size] for i in range(0, len(lines), chunk_size)
            ]

            results = []
            for chunk in chunks:
                chunk_result = parser_func(chunk)
                if chunk_result:
                    results.append(chunk_result)

            # 結果統合（簡易版）
            if results:
                return results[0]  # 最初の有効な結果を使用

            return None

        except Exception as e:
            self.logger.warning(f"大容量パーシング最適化に失敗、フォールバック: {e}")
            return parser_func(content)

    # ========== メモリ最適化 ==========

    def optimize_memory_usage(self) -> Dict[str, Any]:
        """
        メモリ使用量最適化

        Returns:
            最適化結果
        """
        try:
            initial_cache_size = len(self._operation_cache)

            # 古いキャッシュエントリの削除（簡易版LRU）
            if len(self._operation_cache) > 100:
                # 最近使用されたもの以外を削除
                cache_items = list(self._operation_cache.items())
                recent_items = cache_items[-50:]  # 最新50項目を保持
                self._operation_cache = dict(recent_items)

            optimized_size = len(self._operation_cache)

            return {
                "cache_cleaned": True,
                "initial_cache_size": initial_cache_size,
                "optimized_cache_size": optimized_size,
                "memory_freed": initial_cache_size - optimized_size,
            }

        except Exception as e:
            self.logger.error(f"メモリ最適化中にエラー: {e}")
            return {"cache_cleaned": False, "error": str(e)}

    # ========== パフォーマンス監視 ==========

    def performance_monitor(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """
        関数実行パフォーマンス監視デコレーター

        Args:
            func: 監視対象関数

        Returns:
            監視付き関数
        """

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not self.performance_monitoring:
                return func(*args, **kwargs)

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # メトリクス記録
                self._record_metrics(
                    func.__name__,
                    execution_time,
                    self._estimate_memory_usage(result),
                    self._estimate_input_size(args, kwargs),
                    False,
                )

                return result

            except Exception as e:
                execution_time = time.time() - start_time
                self.logger.error(f"監視対象関数でエラー ({func.__name__}): {e}")
                self._record_metrics(func.__name__, execution_time, 0, 0, False)
                raise

        return wrapper

    def _record_metrics(
        self,
        operation_name: str,
        execution_time: float,
        memory_usage: int,
        input_size: int,
        optimization_applied: bool,
    ) -> None:
        """パフォーマンスメトリクスの記録"""
        metric = PerformanceMetrics(
            operation_name=operation_name,
            execution_time=execution_time,
            memory_usage=memory_usage,
            input_size=input_size,
            optimization_applied=optimization_applied,
        )

        self._metrics.append(metric)

        # メトリクス数制限（メモリ節約）
        if len(self._metrics) > 1000:
            self._metrics = self._metrics[-500:]  # 最新500件を保持

    # ========== 統計・情報取得 ==========

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """最適化統計情報を取得"""
        if not self._metrics:
            return {"total_operations": 0, "optimization_rate": 0.0}

        total_ops = len(self._metrics)
        optimized_ops = sum(1 for m in self._metrics if m.optimization_applied)

        avg_execution_time = sum(m.execution_time for m in self._metrics) / total_ops

        return {
            "total_operations": total_ops,
            "optimized_operations": optimized_ops,
            "optimization_rate": optimized_ops / total_ops,
            "avg_execution_time": avg_execution_time,
            "cache_size": len(self._operation_cache),
            "config": {
                "caching_enabled": self.enable_caching,
                "parallel_enabled": self.enable_parallel,
                "memory_limit_mb": self.memory_limit,
            },
        }

    def clear_optimization_cache(self) -> None:
        """最適化キャッシュをクリア"""
        self._operation_cache.clear()
        self._metrics.clear()
        self.logger.info("最適化キャッシュをクリアしました")

    def _estimate_memory_usage(self, obj: Any) -> int:
        """オブジェクトのメモリ使用量推定（簡易版）"""
        try:
            import sys

            return sys.getsizeof(obj)
        except Exception:
            return 0

    def _estimate_input_size(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> int:
        """入力サイズの推定"""
        try:
            total_size = 0
            for arg in args:
                if isinstance(arg, str):
                    total_size += len(arg)
                elif isinstance(arg, list) and arg and isinstance(arg[0], str):
                    total_size += sum(len(line) for line in arg)
            return total_size
        except Exception:
            return 0
