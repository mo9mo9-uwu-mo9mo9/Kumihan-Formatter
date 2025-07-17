"""
ベンチマーク - キャッシュ関連機能

キャッシュパフォーマンス関連のベンチマーク機能を管理
Issue #476対応 - ファイルサイズ制限遵守
"""

import statistics
import time
from pathlib import Path
from typing import Any, Callable

from ..caching.file_cache import FileCache
from ..caching.parse_cache import ParseCache
from ..caching.render_cache import RenderCache
from ..utilities.logger import get_logger
from .benchmark_types import BenchmarkConfig, BenchmarkResult
from .memory_monitor import MemoryMonitor
from .profiler import AdvancedProfiler


class BenchmarkCache:
    """キャッシュ関連ベンチマーク機能

    機能:
    - キャッシュパフォーマンステスト
    - キャッシュヒット率テスト
    - キャッシュ統計取得
    """

    def __init__(
        self,
        config: BenchmarkConfig,
        file_cache: FileCache | None = None,
        parse_cache: ParseCache | None = None,
        render_cache: RenderCache | None = None,
        memory_monitor: MemoryMonitor | None = None,
        profiler: AdvancedProfiler | None = None,
    ):
        """キャッシュベンチマークを初期化"""
        self.logger = get_logger(__name__)
        self.config = config
        self.file_cache = file_cache
        self.parse_cache = parse_cache
        self.render_cache = render_cache
        self.memory_monitor = memory_monitor
        self.profiler = profiler

    def run_cache_benchmarks(self) -> list[BenchmarkResult]:
        """キャッシュパフォーマンステスト"""
        if not self.config.cache_enabled:
            print("  Cache disabled, skipping cache benchmarks")
            return []

        # キャッシュヒット率テスト
        result = self.benchmark_cache_performance()
        print(f"  Cache performance: {result.avg_time:.3f}s avg")
        return [result]

    def benchmark_cache_performance(self) -> BenchmarkResult:
        """キャッシュパフォーマンステスト"""
        name = "cache_performance"

        # キャッシュを事前にウォームアップ
        test_content = self._generate_test_content("medium")
        test_file = None

        if self.file_cache:
            test_file = Path("/tmp/benchmark_cache.txt")
            test_file.write_text(test_content, encoding="utf-8")
            # 一度読み込んでキャッシュに保存
            self.file_cache.get_file_content(test_file)

        if self.parse_cache:
            # 一度パースしてキャッシュに保存
            self.parse_cache.get_parse_or_compute(
                test_content, self._mock_parse_function
            )

        def benchmark_func() -> str:
            # キャッシュヒットを期待
            if self.file_cache and test_file:
                self.file_cache.get_file_content(test_file)

            if self.parse_cache:
                self.parse_cache.get_parse_or_compute(
                    test_content, self._mock_parse_function
                )

            return "cached_result"

        return self._run_benchmark(name, benchmark_func)

    def _run_benchmark(self, name: str, func: Callable[[], Any]) -> BenchmarkResult:
        """ベンチマークを実行"""
        # ウォームアップ
        self.logger.debug(f"ウォームアップ開始: {self.config.warmup_iterations}回")
        for i in range(self.config.warmup_iterations):
            func()
            self.logger.debug(
                f"ウォームアップ {i+1}/{self.config.warmup_iterations} 完了"
            )

        # メモリ監視開始
        start_memory = None
        if self.memory_monitor:
            start_memory = self.memory_monitor.take_snapshot()

        # プロファイリング開始
        session_name = f"benchmark_{name}"
        profiler_context = None
        if self.profiler:
            profiler_context = self.profiler.profile_session(session_name)
            profiler_context.__enter__()

        # 実際の測定
        self.logger.debug(f"ベンチマーク測定開始: {self.config.iterations}回")
        times = []
        for i in range(self.config.iterations):
            start_time = time.perf_counter()
            func()
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            times.append(execution_time)
            self.logger.debug(
                f"実行 {i+1}/{self.config.iterations}: {execution_time:.3f}s"
            )

        # プロファイリング終了
        if profiler_context:
            profiler_context.__exit__(None, None, None)

        # メモリ監視終了
        end_memory = None
        if self.memory_monitor:
            end_memory = self.memory_monitor.take_snapshot()

        # 統計計算
        total_time = sum(times)
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_dev = statistics.stdev(times) if len(times) > 1 else 0.0

        # メモリ使用量計算
        memory_usage = {}
        if start_memory and end_memory:
            memory_usage = {
                "start_mb": start_memory.memory_mb,
                "end_mb": end_memory.memory_mb,
                "peak_mb": max(start_memory.memory_mb, end_memory.memory_mb),
                "increase_mb": end_memory.memory_mb - start_memory.memory_mb,
            }

        # キャッシュ統計を取得
        cache_stats = self._get_cache_stats()

        # スループット計算
        throughput = self.config.iterations / total_time if total_time > 0 else None

        result = BenchmarkResult(
            name=name,
            iterations=self.config.iterations,
            total_time=total_time,
            avg_time=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_dev=std_dev,
            memory_usage=memory_usage,
            cache_stats=cache_stats,
            throughput=throughput,
        )

        self.logger.info(
            f"ベンチマーク完了: {name}, avg={avg_time:.3f}s, "
            f"throughput={throughput:.1f}ops/s"
            if throughput
            else ""
        )

        return result

    def _get_cache_stats(self) -> dict[str, Any]:
        """キャッシュ統計を取得"""
        stats = {}

        if self.file_cache:
            file_stats = self.file_cache.get_stats()
            stats["file_cache"] = file_stats

        if self.parse_cache:
            parse_stats = self.parse_cache.get_stats()
            stats["parse_cache"] = parse_stats

        if self.render_cache:
            render_stats = self.render_cache.get_stats()
            stats["render_cache"] = render_stats

        return stats

    def _generate_test_content(self, size: str) -> str:
        """テストコンテンツを生成"""
        base_content = "これはテストコンテンツです。"

        if size == "small":
            return base_content * 10  # 約240文字
        elif size == "medium":
            return base_content * 100  # 約2.4KB
        elif size == "large":
            return base_content * 1000  # 約24KB
        else:
            return base_content * 100

    def _mock_parse_function(self, content: str) -> Any:
        """モックパース関数"""
        # 簡単なパース処理をシミュレート
        lines = content.split("\n")
        return [
            {"type": "text", "content": line, "index": i}
            for i, line in enumerate(lines)
        ]
