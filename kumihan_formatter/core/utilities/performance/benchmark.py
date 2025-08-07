"""
パフォーマンスベンチマーク・テストシステム
Issue #813対応 - performance_metrics.py分割版（ベンチマーク系）

責任範囲:
- パフォーマンステスト実行
- ベンチマーク結果分析
- 性能比較・評価
- 最適化効果測定
"""

import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ..logger import get_logger


@dataclass
class BenchmarkResult:
    """ベンチマーク結果"""

    name: str
    execution_time: float
    iterations: int
    avg_time_per_iteration: float
    min_time: float
    max_time: float
    std_deviation: float
    memory_usage_mb: Optional[float] = None
    success_rate: float = 100.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceBenchmark:
    """
    パフォーマンステスト・ベンチマークシステム

    機能:
    - 関数・メソッドの性能測定
    - 複数回実行による統計分析
    - メモリ使用量監視
    - パフォーマンス比較レポート
    """

    def __init__(self, default_iterations: int = 100):
        self.logger = get_logger(__name__)
        self.default_iterations = default_iterations
        self.results: List[BenchmarkResult] = []

        # パフォーマンス監視
        self._memory_available = self._check_memory_monitoring()

        self.logger.info(
            f"PerformanceBenchmark initialized with {default_iterations} default iterations"
        )

    def _check_memory_monitoring(self) -> bool:
        """メモリ監視機能の利用可能性をチェック"""
        try:
            import psutil  # noqa: F401

            return True
        except ImportError:
            self.logger.warning("psutil not available, memory monitoring disabled")
            return False

    def benchmark_function(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        iterations: Optional[int] = None,
        name: Optional[str] = None,
        warm_up: int = 5,
    ) -> BenchmarkResult:
        """
        関数のベンチマーク実行

        Args:
            func: ベンチマーク対象関数
            args: 関数引数
            kwargs: 関数キーワード引数
            iterations: 実行回数
            name: ベンチマーク名
            warm_up: ウォームアップ実行回数

        Returns:
            BenchmarkResult: ベンチマーク結果
        """
        if kwargs is None:
            kwargs = {}
        if iterations is None:
            iterations = self.default_iterations
        if name is None:
            name = func.__name__

        self.logger.info(f"Starting benchmark: {name} ({iterations} iterations)")

        # ウォームアップ実行
        for _ in range(warm_up):
            try:
                func(*args, **kwargs)
            except Exception:
                pass  # ウォームアップではエラーを無視

        # メモリ使用量の初期値
        initial_memory = self._get_memory_usage()

        # ベンチマーク実行
        execution_times = []
        successful_runs = 0

        start_time = time.time()

        for i in range(iterations):
            iteration_start = time.perf_counter()

            try:
                func(*args, **kwargs)
                iteration_end = time.perf_counter()
                execution_times.append(iteration_end - iteration_start)
                successful_runs += 1

            except Exception as e:
                self.logger.warning(f"Benchmark iteration {i+1} failed: {e}")

        total_time = time.time() - start_time

        # 統計計算
        if execution_times:
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            std_dev = (
                statistics.stdev(execution_times) if len(execution_times) > 1 else 0.0
            )
        else:
            avg_time = min_time = max_time = std_dev = 0.0

        # 成功率計算
        success_rate = (successful_runs / iterations) * 100 if iterations > 0 else 0.0

        # 最終メモリ使用量
        final_memory = self._get_memory_usage()
        memory_delta = final_memory - initial_memory if self._memory_available else None

        # 結果作成
        result = BenchmarkResult(
            name=name,
            execution_time=total_time,
            iterations=iterations,
            avg_time_per_iteration=avg_time,
            min_time=min_time,
            max_time=max_time,
            std_deviation=std_dev,
            memory_usage_mb=memory_delta,
            success_rate=success_rate,
            metadata={
                "successful_runs": successful_runs,
                "failed_runs": iterations - successful_runs,
                "warm_up_iterations": warm_up,
            },
        )

        self.results.append(result)

        self.logger.info(
            f"Benchmark completed: {name} - "
            f"avg: {avg_time:.4f}s, "
            f"success: {success_rate:.1f}%"
        )

        return result

    def _get_memory_usage(self) -> float:
        """現在のメモリ使用量を取得（MB）"""
        if not self._memory_available:
            return 0.0

        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def benchmark_multiple_functions(
        self,
        functions: Dict[str, Callable],
        args: tuple = (),
        kwargs: dict = None,
        iterations: Optional[int] = None,
    ) -> Dict[str, BenchmarkResult]:
        """
        複数関数の比較ベンチマーク

        Args:
            functions: {名前: 関数} の辞書
            args: 共通引数
            kwargs: 共通キーワード引数
            iterations: 実行回数

        Returns:
            Dict[str, BenchmarkResult]: 各関数の結果
        """
        if kwargs is None:
            kwargs = {}

        results = {}

        for name, func in functions.items():
            result = self.benchmark_function(
                func=func, args=args, kwargs=kwargs, iterations=iterations, name=name
            )
            results[name] = result

        return results

    def compare_performance(self, baseline_name: str) -> str:
        """
        ベースライン関数との性能比較レポートを生成

        Args:
            baseline_name: ベースライン関数名

        Returns:
            str: 比較レポート
        """
        baseline = None
        for result in self.results:
            if result.name == baseline_name:
                baseline = result
                break

        if baseline is None:
            return f"Baseline '{baseline_name}' not found in results"

        report_lines = [
            f"📊 パフォーマンス比較レポート (ベースライン: {baseline_name})",
            "=" * 60,
            f"ベースライン: {baseline.avg_time_per_iteration:.4f}s",
            "",
        ]

        for result in self.results:
            if result.name == baseline_name:
                continue

            if baseline.avg_time_per_iteration > 0:
                speedup = (
                    baseline.avg_time_per_iteration / result.avg_time_per_iteration
                )
                speedup_percent = (speedup - 1) * 100

                if speedup > 1:
                    performance_text = (
                        f"{speedup:.2f}x faster ({speedup_percent:.1f}% improvement)"
                    )
                else:
                    slowdown_percent = (1 - speedup) * 100
                    performance_text = (
                        f"{1/speedup:.2f}x slower ({slowdown_percent:.1f}% slower)"
                    )
            else:
                performance_text = "比較不可能"

            report_lines.extend(
                [
                    f"{result.name}:",
                    f"  平均時間: {result.avg_time_per_iteration:.4f}s",
                    f"  パフォーマンス: {performance_text}",
                    f"  成功率: {result.success_rate:.1f}%",
                    "",
                ]
            )

        return "\n".join(report_lines)

    def get_summary_report(self) -> str:
        """全体的な統計レポートを生成"""
        if not self.results:
            return "ベンチマーク結果がありません"

        report_lines = [
            "📈 ベンチマーク統計レポート",
            "=" * 40,
            f"総実行テスト数: {len(self.results)}",
            "",
        ]

        # 最速・最遅の関数
        fastest = min(self.results, key=lambda x: x.avg_time_per_iteration)
        slowest = max(self.results, key=lambda x: x.avg_time_per_iteration)

        report_lines.extend(
            [
                f"🏆 最高性能: {fastest.name} ({fastest.avg_time_per_iteration:.4f}s)",
                f"🐌 最低性能: {slowest.name} ({slowest.avg_time_per_iteration:.4f}s)",
                "",
            ]
        )

        # 各結果の詳細
        for result in sorted(self.results, key=lambda x: x.avg_time_per_iteration):
            memory_info = (
                f", メモリ: {result.memory_usage_mb:.2f}MB"
                if result.memory_usage_mb
                else ""
            )

            report_lines.append(
                f"{result.name}: {result.avg_time_per_iteration:.4f}s "
                f"(成功率: {result.success_rate:.1f}%{memory_info})"
            )

        return "\n".join(report_lines)

    def clear_results(self):
        """結果をクリア"""
        cleared_count = len(self.results)
        self.results.clear()
        self.logger.info(f"Cleared {cleared_count} benchmark results")

    def export_results_to_dict(self) -> List[Dict[str, Any]]:
        """結果を辞書形式でエクスポート"""
        return [
            {
                "name": result.name,
                "execution_time": result.execution_time,
                "iterations": result.iterations,
                "avg_time_per_iteration": result.avg_time_per_iteration,
                "min_time": result.min_time,
                "max_time": result.max_time,
                "std_deviation": result.std_deviation,
                "memory_usage_mb": result.memory_usage_mb,
                "success_rate": result.success_rate,
                "metadata": result.metadata,
            }
            for result in self.results
        ]
