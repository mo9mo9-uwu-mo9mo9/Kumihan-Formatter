"""ベンチマーク実行エンジン

Single Responsibility Principle適用: ベンチマーク実行の責任分離
Issue #476 Phase2対応 - パフォーマンスモジュール統合
"""

import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ...utilities.logger import get_logger
from ..core.base import PerformanceComponent, PerformanceMetric
from ..core.metrics import BenchmarkConfig, BenchmarkResult
from ..core.persistence import BaselineManager, get_global_persistence
from ..monitoring.memory import MemoryMonitor
from ..profiler import AdvancedProfiler
from .analysis import BaselineHelper, BenchmarkAnalyzer
from .cache_stats import CacheStatsCollector


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

        # ベースライン管理と分析エンジン
        self.baseline_manager = BaselineManager(get_global_persistence())
        self.analyzer = BenchmarkAnalyzer(self.baseline_manager)
        self.baseline_helper = BaselineHelper(self.baseline_manager)
        self.cache_collector = CacheStatsCollector(self.benchmark_config.cache_enabled)

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

        # プロファイリング開始（将来の拡張用）
        if self.profiler:
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

        # プロファイリング終了（将来の拡張用）
        if self.profiler:
            pass

        # メモリ監視終了
        memory_usage = {}
        if self.memory_monitor:
            self.memory_monitor.stop_monitoring()
            memory_usage = self.memory_monitor.get_memory_usage()

        # キャッシュ統計（必要に応じて）
        cache_stats = self.cache_collector.collect_cache_stats()

        # 結果の分析
        result = self.analyzer.analyze_results(
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

    def compare_with_baseline(self, baseline_name: str) -> Dict[str, Any]:
        """ベースラインと比較

        Args:
            baseline_name: ベースライン名

        Returns:
            比較結果
        """
        return self.analyzer.compare_with_baseline(self.results, baseline_name)

    def save_as_baseline(self, name: str) -> Path:
        """現在の結果をベースラインとして保存

        Args:
            name: ベースライン名

        Returns:
            保存したファイルのパス
        """
        return self.baseline_helper.save_as_baseline(
            name, self.results, self.benchmark_config.to_dict()
        )

    def collect_metrics(self) -> List[PerformanceMetric]:
        """メトリクスを収集

        Returns:
            収集されたメトリクス
        """
        return self.analyzer.collect_metrics(self.results)

    def generate_report(self) -> Dict[str, Any]:
        """ベンチマークレポートを生成

        Returns:
            レポートデータ
        """
        base_report = self.analyzer.generate_report(self.results)
        if "message" in base_report:
            return base_report

        # 設定とシステム情報を追加
        base_report["config"] = self.benchmark_config.to_dict()
        base_report["system_info"] = self.baseline_helper._get_system_info()

        return base_report

    def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        if self.memory_monitor:
            self.memory_monitor.cleanup()
        self.results.clear()
        super().cleanup()
