"""
アルゴリズム最適化システム - Issue #922 Phase 4-6対応
動的アルゴリズム選択・パフォーマンス監視による最適化システム
"""

import cProfile
import functools
import gc
import pstats
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    TypeVar,
    cast,
)

import psutil

from kumihan_formatter.core.utilities.logger import get_logger

T = TypeVar("T")
R = TypeVar("R")
F = TypeVar("F", bound=Callable[..., Any])


class OptimizationLevel(Enum):
    """最適化レベル"""

    NONE = auto()  # 最適化なし
    BASIC = auto()  # 基本最適化
    ADVANCED = auto()  # 高度な最適化
    AGGRESSIVE = auto()  # 積極的最適化
    ADAPTIVE = auto()  # 適応的最適化


class AlgorithmType(Enum):
    """アルゴリズムタイプ"""

    PARSING = auto()  # パース処理
    RENDERING = auto()  # レンダリング処理
    VALIDATION = auto()  # 検証処理
    TRANSFORMATION = auto()  # 変換処理
    SORTING = auto()  # ソート処理
    SEARCHING = auto()  # 検索処理


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""

    execution_time: float = 0.0
    memory_usage: int = 0  # bytes
    cpu_usage: float = 0.0  # percentage
    io_operations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    error_count: int = 0
    throughput: float = 0.0  # operations per second

    @property
    def efficiency_score(self) -> float:
        """効率性スコア（0-100）"""
        if self.execution_time <= 0:
            return 0.0

        # 基本スコア（実行時間の逆数ベース）
        time_score = min(100.0, 1000.0 / self.execution_time)

        # メモリ使用量ペナルティ
        memory_penalty = min(50.0, self.memory_usage / (1024 * 1024))  # MB単位

        # キャッシュヒット率ボーナス
        cache_bonus = 0.0
        if self.cache_hits + self.cache_misses > 0:
            hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses)
            cache_bonus = hit_rate * 20.0

        # エラー率ペナルティ
        error_penalty = self.error_count * 10.0

        score = time_score + cache_bonus - memory_penalty - error_penalty
        return max(0.0, min(100.0, score))


@dataclass
class AlgorithmProfile:
    """アルゴリズムプロファイル"""

    algorithm_name: str
    algorithm_type: AlgorithmType
    complexity_class: str = "O(n)"
    best_case_size: int = 0
    worst_case_size: int = float("inf")  # type: ignore
    memory_requirement: int = 0  # bytes
    is_thread_safe: bool = False
    performance_history: List[PerformanceMetrics] = field(default_factory=list)

    @property
    def average_performance(self) -> PerformanceMetrics:
        """平均パフォーマンス"""
        if not self.performance_history:
            return PerformanceMetrics()

        count = len(self.performance_history)
        return PerformanceMetrics(
            execution_time=sum(m.execution_time for m in self.performance_history)
            / count,
            memory_usage=int(
                sum(m.memory_usage for m in self.performance_history) / count
            ),
            cpu_usage=sum(m.cpu_usage for m in self.performance_history) / count,
            throughput=sum(m.throughput for m in self.performance_history) / count,
        )


class OptimizationStrategy(ABC):
    """最適化戦略の抽象基底クラス"""

    @abstractmethod
    def should_optimize(self, metrics: PerformanceMetrics) -> bool:
        """最適化すべきかを判定"""
        pass

    @abstractmethod
    def optimize(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Callable[..., Any]:
        """最適化を適用"""
        pass


class MemoryOptimizationStrategy(OptimizationStrategy):
    """メモリ最適化戦略"""

    def __init__(self, memory_threshold_mb: float = 100.0) -> None:
        self.memory_threshold_bytes = memory_threshold_mb * 1024 * 1024

    def should_optimize(self, metrics: PerformanceMetrics) -> bool:
        return metrics.memory_usage > self.memory_threshold_bytes

    def optimize(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Callable[..., Any]:
        @functools.wraps(func)
        def optimized_func(*args: Any, **kwargs: Any) -> Any:
            # ガベージコレクション実行
            gc.collect()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # 明示的なメモリクリーンアップ
                gc.collect()

        return optimized_func


class CacheOptimizationStrategy(OptimizationStrategy):
    """キャッシュ最適化戦略"""

    def __init__(self, cache_size: int = 1000) -> None:
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.cache_size = cache_size
        self.access_order = deque()  # type: ignore

    def should_optimize(self, metrics: PerformanceMetrics) -> bool:
        # キャッシュヒット率が低い場合に最適化
        if metrics.cache_hits + metrics.cache_misses == 0:
            return True

        hit_rate = metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses)
        return hit_rate < 0.5

    def optimize(
        self, func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Callable[..., Any]:
        @functools.wraps(func)
        def cached_func(*args: Any, **kwargs: Any) -> Any:
            # キャッシュキー生成
            cache_key = self._generate_cache_key(func, args, kwargs)

            # キャッシュヒット確認
            if cache_key in self.cache:
                value, timestamp = self.cache[cache_key]
                # TTL チェック（30秒）
                if time.time() - timestamp < 30:
                    return value
                else:
                    del self.cache[cache_key]

            # 実際の関数実行
            result = func(*args, **kwargs)

            # キャッシュサイズ制限
            if len(self.cache) >= self.cache_size:
                # LRU削除
                oldest_key = self.access_order.popleft()
                self.cache.pop(oldest_key, None)

            # キャッシュに保存
            self.cache[cache_key] = (result, time.time())
            self.access_order.append(cache_key)

            return result

        return cached_func

    def _generate_cache_key(
        self, func: Callable[..., Any], args: Any, kwargs: Any
    ) -> str:
        """キャッシュキー生成"""
        func_name = func.__name__
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))
        return f"{func_name}:{hash(args_str + kwargs_str)}"


class AlgorithmOptimizer:
    """
    アルゴリズム最適化システム

    機能:
    - 動的アルゴリズム選択
    - パフォーマンスプロファイリング
    - 適応的最適化
    - メモリ・CPU最適化
    """

    def __init__(
        self,
        optimization_level: OptimizationLevel = OptimizationLevel.BASIC,
        enable_profiling: bool = True,
        profile_output_dir: Optional[Path] = None,
    ) -> None:
        """
        アルゴリズム最適化システムの初期化

        Args:
            optimization_level: 最適化レベル
            enable_profiling: プロファイリング有効フラグ
            profile_output_dir: プロファイル出力ディレクトリ
        """
        self.logger = get_logger(__name__)
        self.optimization_level = optimization_level
        self.enable_profiling = enable_profiling
        self.profile_output_dir = profile_output_dir or Path("tmp/profiles")

        # アルゴリズム登録
        self.algorithms: Dict[str, List[AlgorithmProfile]] = defaultdict(list)
        self.active_algorithms: Dict[str, AlgorithmProfile] = {}

        # 最適化戦略
        self.optimization_strategies: List[OptimizationStrategy] = [
            MemoryOptimizationStrategy(),
            CacheOptimizationStrategy(),
        ]

        # プロファイリング
        self.profiler_data: Dict[str, Any] = {}
        self._profiling_lock = threading.Lock()

        # 統計情報
        self.optimization_stats = {
            "total_optimizations": 0,
            "successful_optimizations": 0,
            "performance_improvements": 0,
            "memory_savings": 0,
        }

        # 出力ディレクトリ作成
        self.profile_output_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(
            f"Algorithm optimizer initialized: level={optimization_level.name}, "
            f"profiling={enable_profiling}"
        )

    def register_algorithm(
        self,
        algorithm_name: str,
        algorithm_func: Callable[..., Any],
        algorithm_type: AlgorithmType,
        complexity_class: str = "O(n)",
        memory_requirement: int = 0,
        is_thread_safe: bool = False,
    ) -> None:
        """
        アルゴリズムを登録

        Args:
            algorithm_name: アルゴリズム名
            algorithm_func: アルゴリズム関数
            algorithm_type: アルゴリズムタイプ
            complexity_class: 計算量クラス
            memory_requirement: メモリ要件（バイト）
            is_thread_safe: スレッドセーフフラグ
        """
        profile = AlgorithmProfile(
            algorithm_name=algorithm_name,
            algorithm_type=algorithm_type,
            complexity_class=complexity_class,
            memory_requirement=memory_requirement,
            is_thread_safe=is_thread_safe,
        )

        type_key = algorithm_type.name
        self.algorithms[type_key].append(profile)

        # 最適化された関数を作成
        optimized_func = self._create_optimized_function(algorithm_func, profile)
        setattr(self, f"{algorithm_name}_optimized", optimized_func)

        self.logger.info(f"Algorithm registered: {algorithm_name} ({type_key})")

    def select_best_algorithm(
        self,
        algorithm_type: AlgorithmType,
        data_size: int,
        memory_limit: Optional[int] = None,
        thread_safe_required: bool = False,
    ) -> Optional[AlgorithmProfile]:
        """
        最適なアルゴリズムを選択

        Args:
            algorithm_type: アルゴリズムタイプ
            data_size: データサイズ
            memory_limit: メモリ制限（バイト）
            thread_safe_required: スレッドセーフ要件

        Returns:
            Optional[AlgorithmProfile]: 最適なアルゴリズムプロファイル
        """
        type_key = algorithm_type.name
        candidates = self.algorithms.get(type_key, [])

        if not candidates:
            self.logger.warning(f"No algorithms registered for type: {type_key}")
            return None

        # フィルタリング
        filtered_candidates = []
        for profile in candidates:
            # データサイズチェック
            if profile.best_case_size <= data_size <= profile.worst_case_size:
                # メモリ制限チェック
                if memory_limit is None or profile.memory_requirement <= memory_limit:
                    # スレッドセーフ要件チェック
                    if not thread_safe_required or profile.is_thread_safe:
                        filtered_candidates.append(profile)

        if not filtered_candidates:
            self.logger.warning(
                "No suitable algorithms found for the given constraints"
            )
            return None

        # 最適アルゴリズム選択
        best_algorithm = max(
            filtered_candidates, key=lambda p: p.average_performance.efficiency_score
        )

        self.logger.info(
            f"Selected algorithm: {best_algorithm.algorithm_name} "
            f"(efficiency: {best_algorithm.average_performance.efficiency_score:.2f})"
        )

        return best_algorithm

    def profile_function(
        self, func: F, *args: Any, **kwargs: Any
    ) -> Tuple[Any, PerformanceMetrics]:
        """
        関数のパフォーマンスプロファイリング

        Args:
            func: プロファイル対象関数
            *args: 引数
            **kwargs: キーワード引数

        Returns:
            Tuple[Any, PerformanceMetrics]: 実行結果と性能メトリクス
        """
        if not self.enable_profiling:
            result = func(*args, **kwargs)
            return result, PerformanceMetrics()

        func_name = func.__name__

        # メモリ使用量測定開始
        process = psutil.Process()
        memory_before = process.memory_info().rss

        # プロファイリング開始
        profiler = cProfile.Profile()
        profiler.enable()

        start_time = time.time()

        try:
            result = func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Function execution error in {func_name}: {e}")
            raise
        finally:
            end_time = time.time()
            profiler.disable()

        # メモリ使用量測定終了
        memory_after = process.memory_info().rss

        # パフォーマンスメトリクス作成
        execution_time = end_time - start_time
        memory_usage = max(0, memory_after - memory_before)

        metrics = PerformanceMetrics(
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=process.cpu_percent(),
        )

        # プロファイル結果保存
        self._save_profile_results(func_name, profiler, metrics)

        self.logger.debug(
            f"Profiled {func_name}: {execution_time:.4f}s, "
            f"{memory_usage / 1024 / 1024:.2f}MB"
        )

        return result, metrics

    def optimize_function(self, func: F) -> F:
        """
        関数の最適化デコレータ

        Args:
            func: 最適化対象関数

        Returns:
            F: 最適化された関数
        """

        @functools.wraps(func)
        def optimized_wrapper(*args: Any, **kwargs: Any) -> Any:
            # 基本プロファイリング
            result, metrics = self.profile_function(func, *args, **kwargs)

            # 最適化戦略適用
            if self.optimization_level != OptimizationLevel.NONE:
                for strategy in self.optimization_strategies:
                    if strategy.should_optimize(metrics):
                        optimized_func = strategy.optimize(func, *args, **kwargs)
                        # 最適化後の再実行（比較のため）
                        optimized_result, optimized_metrics = self.profile_function(
                            optimized_func, *args, **kwargs
                        )

                        # 改善があれば採用
                        if (
                            optimized_metrics.efficiency_score
                            > metrics.efficiency_score
                        ):
                            self.optimization_stats["performance_improvements"] += 1
                            return optimized_result

            self.optimization_stats["total_optimizations"] += 1
            return result

        return cast(F, optimized_wrapper)

    def benchmark_algorithms(
        self,
        algorithm_type: AlgorithmType,
        test_data_sizes: List[int],
        test_iterations: int = 5,
    ) -> Dict[str, List[PerformanceMetrics]]:
        """
        アルゴリズムベンチマーク実行

        Args:
            algorithm_type: ベンチマーク対象アルゴリズムタイプ
            test_data_sizes: テストデータサイズリスト
            test_iterations: テスト反復回数

        Returns:
            Dict[str, List[PerformanceMetrics]]: ベンチマーク結果
        """
        type_key = algorithm_type.name
        candidates = self.algorithms.get(type_key, [])

        if not candidates:
            self.logger.warning(f"No algorithms to benchmark for type: {type_key}")
            return {}

        self.logger.info(
            f"Starting benchmark for {len(candidates)} algorithms "
            f"with {len(test_data_sizes)} data sizes"
        )

        benchmark_results: Dict[str, List[PerformanceMetrics]] = {}

        for profile in candidates:
            algorithm_name = profile.algorithm_name
            benchmark_results[algorithm_name] = []

            for data_size in test_data_sizes:
                iteration_metrics = []

                for iteration in range(test_iterations):
                    # テストデータ生成
                    test_data = self._generate_test_data(algorithm_type, data_size)

                    # アルゴリズム取得
                    algorithm_func = getattr(self, f"{algorithm_name}_optimized", None)
                    if algorithm_func is None:
                        self.logger.warning(
                            f"Algorithm function not found: {algorithm_name}"
                        )
                        continue

                    # ベンチマーク実行
                    try:
                        _, metrics = self.profile_function(algorithm_func, test_data)
                        iteration_metrics.append(metrics)
                    except Exception as e:
                        self.logger.error(
                            f"Benchmark error for {algorithm_name} "
                            f"(size={data_size}, iter={iteration}): {e}"
                        )

                # 平均メトリクス計算
                if iteration_metrics:
                    avg_metrics = self._calculate_average_metrics(iteration_metrics)
                    benchmark_results[algorithm_name].append(avg_metrics)

                    # プロファイルに追加
                    profile.performance_history.append(avg_metrics)

        self._save_benchmark_results(algorithm_type, benchmark_results)
        return benchmark_results

    def _create_optimized_function(
        self, func: Callable[..., Any], profile: AlgorithmProfile
    ) -> Callable[..., Any]:
        """最適化された関数を作成"""
        if self.optimization_level == OptimizationLevel.NONE:
            return func

        return self.optimize_function(func)

    def _generate_test_data(self, algorithm_type: AlgorithmType, size: int) -> Any:
        """テストデータ生成"""
        if algorithm_type == AlgorithmType.PARSING:
            return "# テスト見出し #内容##\n" * size
        elif algorithm_type == AlgorithmType.SORTING:
            import random

            return [random.randint(1, 1000) for _ in range(size)]
        else:
            return list(range(size))

    def _calculate_average_metrics(
        self, metrics_list: List[PerformanceMetrics]
    ) -> PerformanceMetrics:
        """平均メトリクス計算"""
        if not metrics_list:
            return PerformanceMetrics()

        count = len(metrics_list)
        return PerformanceMetrics(
            execution_time=sum(m.execution_time for m in metrics_list) / count,
            memory_usage=int(sum(m.memory_usage for m in metrics_list) / count),
            cpu_usage=sum(m.cpu_usage for m in metrics_list) / count,
            throughput=sum(m.throughput for m in metrics_list) / count,
        )

    def _save_profile_results(
        self, func_name: str, profiler: cProfile.Profile, metrics: PerformanceMetrics
    ) -> None:
        """プロファイル結果を保存"""
        try:
            profile_file = (
                self.profile_output_dir / f"{func_name}_{int(time.time())}.prof"
            )
            profiler.dump_stats(str(profile_file))

            # テキスト形式でも保存
            with open(profile_file.with_suffix(".txt"), "w") as f:
                stats = pstats.Stats(profiler)
                import sys

                old_stdout = sys.stdout
                sys.stdout = f
                try:
                    stats.print_stats()
                finally:
                    sys.stdout = old_stdout

            self.logger.debug(f"Profile saved: {profile_file}")
        except Exception as e:
            self.logger.warning(f"Failed to save profile for {func_name}: {e}")

    def _save_benchmark_results(
        self,
        algorithm_type: AlgorithmType,
        results: Dict[str, List[PerformanceMetrics]],
    ) -> None:
        """ベンチマーク結果を保存"""
        try:
            import json

            results_file = (
                self.profile_output_dir
                / f"benchmark_{algorithm_type.name}_{int(time.time())}.json"
            )

            # JSONシリアライズ可能な形式に変換
            json_results = {}
            for alg_name, metrics_list in results.items():
                json_results[alg_name] = [
                    {
                        "execution_time": m.execution_time,
                        "memory_usage": m.memory_usage,
                        "cpu_usage": m.cpu_usage,
                        "efficiency_score": m.efficiency_score,
                    }
                    for m in metrics_list
                ]

            with open(results_file, "w") as f:
                json.dump(json_results, f, indent=2)

            self.logger.info(f"Benchmark results saved: {results_file}")
        except Exception as e:
            self.logger.error(f"Failed to save benchmark results: {e}")

    def get_optimization_report(self) -> Dict[str, Any]:
        """
        最適化レポートを取得

        Returns:
            Dict[str, Any]: 最適化レポート
        """
        # 登録済みアルゴリズム統計
        algorithm_stats = {}
        for type_key, profiles in self.algorithms.items():
            algorithm_stats[type_key] = {
                "count": len(profiles),
                "algorithms": [
                    {
                        "name": p.algorithm_name,
                        "complexity": p.complexity_class,
                        "thread_safe": p.is_thread_safe,
                        "avg_efficiency": p.average_performance.efficiency_score,
                        "history_count": len(p.performance_history),
                    }
                    for p in profiles
                ],
            }

        return {
            "optimization_level": self.optimization_level.name,
            "profiling_enabled": self.enable_profiling,
            "total_optimizations": self.optimization_stats["total_optimizations"],
            "successful_optimizations": self.optimization_stats[
                "successful_optimizations"
            ],
            "performance_improvements": self.optimization_stats[
                "performance_improvements"
            ],
            "algorithm_types_count": len(self.algorithms),
            "total_algorithms_count": sum(
                len(profiles) for profiles in self.algorithms.values()
            ),
            "algorithm_stats": algorithm_stats,
            "active_strategies": len(self.optimization_strategies),
            "profile_output_dir": str(self.profile_output_dir),
        }

    def cleanup(self) -> None:
        """リソースクリーンアップ"""
        # プロファイルデータクリア
        with self._profiling_lock:
            self.profiler_data.clear()

        # キャッシュクリア
        for strategy in self.optimization_strategies:
            if hasattr(strategy, "cache"):
                strategy.cache.clear()

        self.logger.info("Algorithm optimizer cleanup completed")

    def __del__(self) -> None:
        """デストラクタでクリーンアップ実行"""
        try:
            self.cleanup()
        except Exception:
            pass  # デストラクタでの例外は無視
