"""ベンチマーク実行エンジン

Single Responsibility Principle適用: ベンチマーク実行の責任分離
Issue #476 Phase2対応 - パフォーマンスモジュール統合
"""

import statistics
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ...utilities.logger import get_logger
from ..core.base import PerformanceComponent, PerformanceMetric
from ..core.metrics import BenchmarkConfig, BenchmarkResult
from ..core.persistence import BaselineManager, get_global_persistence
from ..monitoring.memory import MemoryMonitor
from ..profiler import AdvancedProfiler


class BenchmarkRunner(PerformanceComponent):
    """ベンチマーク実行エンジン

    機能:
    - ベンチマークテストの実行管理
    - パフォーマンス測定の標準化
    - 結果の収集と分析
    """

    def __init__(self, config: BenchmarkConfig | None = None) -> None:
        """ベンチマークランナーを初期化

        Args:
            config: ベンチマーク設定
        """
        super().__init__(config.to_dict() if config else None)
        self.benchmark_config = config or BenchmarkConfig()
        self.results: List[BenchmarkResult] = []

        # パフォーマンス測定ツール
        self.profiler = (
            AdvancedProfiler() if self.benchmark_config.enable_profiling else None
        )
        self.memory_monitor = (
            MemoryMonitor() if self.benchmark_config.enable_memory_monitoring else None
        )

        # ベースライン管理
        self.baseline_manager = BaselineManager(get_global_persistence())

        self.logger.info(
            f"BenchmarkRunner initialized: iterations={self.benchmark_config.iterations}, "
            f"warmup={self.benchmark_config.warmup_iterations}"
        )

    def initialize(self) -> None:
        """ベンチマークランナーを初期化"""
        if self.memory_monitor and not self.memory_monitor.is_initialized:
            self.memory_monitor.initialize()

        self.is_initialized = True
        self.logger.info("BenchmarkRunner initialized successfully")

    def run_benchmark(
        self,
        name: str,
        target_func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> BenchmarkResult:
        """単一のベンチマークを実行

        Args:
            name: ベンチマーク名
            target_func: 測定対象の関数
            *args: 関数の位置引数
            **kwargs: 関数のキーワード引数

        Returns:
            ベンチマーク結果
        """
        self.logger.info(f"Running benchmark: {name}")

        # ウォームアップ
        self._warmup(target_func, *args, **kwargs)

        # メモリ監視開始
        if self.memory_monitor:
            self.memory_monitor.start_monitoring()

        # プロファイリング開始
        if self.profiler:
            # self.profiler.start()
            pass

        # ベンチマーク実行
        times: List[float] = []
        start_total = time.perf_counter()

        for i in range(self.benchmark_config.iterations):
            start = time.perf_counter()
            try:
                result = target_func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Benchmark error in iteration {i}: {e}")
                raise
            end = time.perf_counter()
            times.append(end - start)

        end_total = time.perf_counter()
        total_time = end_total - start_total

        # プロファイリング終了
        if self.profiler:
            # self.profiler.stop()
            pass

        # メモリ監視終了
        memory_usage = {}
        if self.memory_monitor:
            self.memory_monitor.stop_monitoring()
            memory_usage = self.memory_monitor.get_memory_usage()

        # キャッシュ統計（必要に応じて）
        cache_stats = self._collect_cache_stats()

        # 結果の分析
        result = self._analyze_results(
            name=name,
            times=times,
            total_time=total_time,
            memory_usage=memory_usage,
            cache_stats=cache_stats,
        )

        self.results.append(result)
        return result

    def run_suite(
        self, benchmarks: Dict[str, Callable[..., Any]], **common_kwargs: Any
    ) -> List[BenchmarkResult]:
        """ベンチマークスイートを実行

        Args:
            benchmarks: ベンチマーク名と関数のマッピング
            **common_kwargs: すべてのベンチマークに共通のキーワード引数

        Returns:
            ベンチマーク結果のリスト
        """
        self.logger.info(f"Running benchmark suite with {len(benchmarks)} benchmarks")

        suite_results = []
        for name, func in benchmarks.items():
            try:
                result = self.run_benchmark(name, func, **common_kwargs)
                suite_results.append(result)
            except Exception as e:
                self.logger.error(f"Failed to run benchmark '{name}': {e}")

        return suite_results

    def _warmup(
        self, target_func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> None:
        """ウォームアップを実行

        Args:
            target_func: ウォームアップ対象の関数
            *args: 関数の位置引数
            **kwargs: 関数のキーワード引数
        """
        if self.benchmark_config.warmup_iterations > 0:
            self.logger.debug(
                f"Running {self.benchmark_config.warmup_iterations} warmup iterations"
            )
            for _ in range(self.benchmark_config.warmup_iterations):
                try:
                    target_func(*args, **kwargs)
                except Exception as e:
                    self.logger.warning(f"Warmup error: {e}")

    def _collect_cache_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を収集

        Returns:
            キャッシュ統計
        """
        cache_stats = {}

        # キャッシュシステムが有効な場合のみ統計を収集
        if self.benchmark_config.cache_enabled:
            # 実際のキャッシュシステムから統計を収集
            # ここでは仮の実装
            cache_stats = {
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
            }

        return cache_stats

    def _analyze_results(
        self,
        name: str,
        times: List[float],
        total_time: float,
        memory_usage: Dict[str, float],
        cache_stats: Dict[str, Any],
    ) -> BenchmarkResult:
        """ベンチマーク結果を分析

        Args:
            name: ベンチマーク名
            times: 各イテレーションの実行時間
            total_time: 総実行時間
            memory_usage: メモリ使用量
            cache_stats: キャッシュ統計

        Returns:
            分析済みベンチマーク結果
        """
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0

        # スループットの計算（必要に応じて）
        throughput = None
        if "operations" in cache_stats:
            throughput = cache_stats["operations"] / total_time

        return BenchmarkResult(
            name=name,
            iterations=len(times),
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            memory_usage=memory_usage,
            cache_stats=cache_stats,
            throughput=throughput,
            regression_score=None,  # 回帰スコアは別途計算
        )

    def compare_with_baseline(self, baseline_name: str) -> Dict[str, Any]:
        """ベースラインと比較

        Args:
            baseline_name: ベースライン名

        Returns:
            比較結果
        """
        baseline_data = self.baseline_manager.load_baseline(baseline_name)
        if not baseline_data:
            self.logger.warning(f"Baseline '{baseline_name}' not found")
            return {}

        comparison_results = {}
        baseline_results = baseline_data.get("data", {}).get("results", [])

        for current_result in self.results:
            # 対応するベースライン結果を探す
            baseline_result = None
            for br in baseline_results:
                if br.get("name") == current_result.name:
                    baseline_result = br
                    break

            if baseline_result:
                comparison = self._compare_single_result(
                    current_result, baseline_result
                )
                comparison_results[current_result.name] = comparison

        return comparison_results

    def _compare_single_result(
        self, current: BenchmarkResult, baseline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """単一の結果を比較

        Args:
            current: 現在の結果
            baseline: ベースライン結果

        Returns:
            比較結果
        """
        baseline_avg = baseline.get("avg_time", 0)
        if baseline_avg == 0:
            return {}

        improvement = ((baseline_avg - current.avg_time) / baseline_avg) * 100
        speedup = baseline_avg / current.avg_time if current.avg_time > 0 else 0

        return {
            "improvement_percent": improvement,
            "speedup": speedup,
            "baseline_avg_time": baseline_avg,
            "current_avg_time": current.avg_time,
            "is_regression": improvement < -5,  # 5%以上遅くなったら回帰
        }

    def save_as_baseline(self, name: str) -> Path:
        """現在の結果をベースラインとして保存

        Args:
            name: ベースライン名

        Returns:
            保存したファイルのパス
        """
        baseline_data = {
            "results": [result.to_dict() for result in self.results],
            "config": self.benchmark_config.to_dict(),
            "system_info": self._get_system_info(),
        }

        return self.baseline_manager.save_baseline(name, baseline_data)

    def _get_system_info(self) -> Dict[str, Any]:
        """システム情報を取得

        Returns:
            システム情報
        """
        from ..core.base import SystemInfo

        return SystemInfo.capture().to_dict()

    def collect_metrics(self) -> List[PerformanceMetric]:
        """メトリクスを収集

        Returns:
            収集されたメトリクス
        """
        metrics = []
        current_time = time.time()

        for result in self.results:
            # 実行時間メトリクス
            metrics.append(
                PerformanceMetric(
                    name=f"{result.name}_avg_time",
                    value=result.avg_time,
                    unit="seconds",
                    timestamp=current_time,
                    category="benchmark",
                    metadata={"benchmark_name": result.name},
                )
            )

            # メモリ使用量メトリクス
            if result.memory_usage:
                for mem_name, mem_value in result.memory_usage.items():
                    metrics.append(
                        PerformanceMetric(
                            name=f"{result.name}_{mem_name}",
                            value=mem_value,
                            unit="MB" if "_mb" in mem_name else "count",
                            timestamp=current_time,
                            category="benchmark_memory",
                            metadata={"benchmark_name": result.name},
                        )
                    )

        return metrics

    def generate_report(self) -> Dict[str, Any]:
        """ベンチマークレポートを生成

        Returns:
            レポートデータ
        """
        if not self.results:
            return {"message": "No benchmark results available"}

        # 結果のサマリー
        summary = {
            "total_benchmarks": len(self.results),
            "total_time": sum(r.total_time for r in self.results),
            "fastest": min(self.results, key=lambda r: r.avg_time).name,
            "slowest": max(self.results, key=lambda r: r.avg_time).name,
        }

        # 詳細結果
        detailed_results = []
        for result in self.results:
            detailed_results.append(
                {
                    "name": result.name,
                    "avg_time": result.avg_time,
                    "min_time": result.min_time,
                    "max_time": result.max_time,
                    "std_dev": result.std_dev,
                    "memory_usage": result.memory_usage,
                    "cache_hit_rate": (
                        result.cache_stats.get("hit_rate", 0)
                        if result.cache_stats
                        else 0
                    ),
                }
            )

        return {
            "summary": summary,
            "results": detailed_results,
            "config": self.benchmark_config.to_dict(),
            "system_info": self._get_system_info(),
        }

    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        if self.memory_monitor:
            self.memory_monitor.cleanup()
        self.results.clear()
        super().cleanup()
