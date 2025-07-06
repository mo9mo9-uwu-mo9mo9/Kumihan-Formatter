"""
ベンチマークテストスイート - パフォーマンス測定

キャッシュ最適化の効果測定とパフォーマンス回帰検出
Issue #402対応 - パフォーマンス最適化
"""

import json
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from ...utilities.logger import get_logger
from ..caching.file_cache import FileCache
from ..caching.parse_cache import ParseCache
from ..caching.render_cache import RenderCache
from ..performance import get_global_monitor
from .memory_monitor import MemoryMonitor
from .profiler import AdvancedProfiler


@dataclass
class BenchmarkResult:
    """ベンチマーク結果"""

    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    std_dev: float
    memory_usage: Dict[str, float]
    cache_stats: Dict[str, Any]
    throughput: Optional[float] = None
    regression_score: Optional[float] = None


@dataclass
class BenchmarkConfig:
    """ベンチマーク設定"""

    iterations: int = 5
    warmup_iterations: int = 2
    enable_profiling: bool = True
    enable_memory_monitoring: bool = True
    cache_enabled: bool = True
    baseline_file: Optional[Path] = None


class PerformanceBenchmarkSuite:
    """パフォーマンスベンチマーク総合スイート

    機能:
    - キャッシュあり/なしの性能比較
    - メモリ使用量の測定
    - プロファイリング統合
    - 回帰検出
    - ベースライン比較
    """

    def __init__(self, config: BenchmarkConfig = None):
        """ベンチマークスイートを初期化

        Args:
            config: ベンチマーク設定
        """
        self.logger = get_logger(__name__)
        self.config = config or BenchmarkConfig()
        self.logger.info(
            f"PerformanceBenchmarkSuite初期化: iterations={self.config.iterations}, warmup={self.config.warmup_iterations}"
        )

        # パフォーマンス測定ツール
        self.monitor = get_global_monitor()
        self.profiler = AdvancedProfiler() if self.config.enable_profiling else None
        self.memory_monitor = (
            MemoryMonitor() if self.config.enable_memory_monitoring else None
        )

        self.logger.debug(
            f"profiling={self.config.enable_profiling}, memory_monitoring={self.config.enable_memory_monitoring}"
        )

        # キャッシュシステム
        self.file_cache = FileCache() if self.config.cache_enabled else None
        self.parse_cache = ParseCache() if self.config.cache_enabled else None
        self.render_cache = RenderCache() if self.config.cache_enabled else None

        # 結果保存
        self.results: List[BenchmarkResult] = []
        self.baseline_results: Optional[Dict[str, BenchmarkResult]] = None

        # ベースラインを読み込み
        if self.config.baseline_file and self.config.baseline_file.exists():
            self.load_baseline(self.config.baseline_file)

        self.logger.info("PerformanceBenchmarkSuite初期化完了")

    def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """完全なベンチマークスイートを実行"""
        self.logger.info("ベンチマークスイート実行開始")
        print("🚀 Starting Performance Benchmark Suite...")
        print("=" * 60)

        # メモリ監視開始
        if self.memory_monitor:
            self.memory_monitor.start_monitoring()
            self.logger.debug("メモリ監視開始")

        try:
            # 1. ファイル読み込みベンチマーク
            self.logger.info("ファイル読み込みベンチマーク開始")
            print("\n📁 File Reading Benchmarks:")
            self._run_file_benchmarks()

            # 2. パースベンチマーク
            self.logger.info("パースベンチマーク開始")
            print("\n🔍 Parsing Benchmarks:")
            self._run_parse_benchmarks()

            # 3. レンダリングベンチマーク
            self.logger.info("レンダリングベンチマーク開始")
            print("\n🎨 Rendering Benchmarks:")
            self._run_render_benchmarks()

            # 4. 統合ベンチマーク
            self.logger.info("エンドツーエンドベンチマーク開始")
            print("\n🔄 End-to-End Benchmarks:")
            self._run_e2e_benchmarks()

            # 5. キャッシュパフォーマンステスト
            self.logger.info("キャッシュパフォーマンステスト開始")
            print("\n💾 Cache Performance Tests:")
            self._run_cache_benchmarks()

        finally:
            # メモリ監視停止
            if self.memory_monitor:
                self.memory_monitor.stop_monitoring()
                self.logger.debug("メモリ監視停止")

        # 結果分析
        analysis = self._analyze_results()
        self.logger.info(
            f"ベンチマークスイート完了: {len(self.results)}個のベンチマークを実行"
        )

        print("\n📊 Benchmark Complete!")
        print("=" * 60)

        return analysis

    def run_regression_test(self) -> Dict[str, Any]:
        """パフォーマンス回帰テストを実行"""
        if not self.baseline_results:
            error_msg = "No baseline results available for regression testing"
            self.logger.error(error_msg)
            return {"error": error_msg}

        self.logger.info("パフォーマンス回帰テスト開始")
        print("🔍 Running Performance Regression Tests...")

        # 主要ベンチマークを実行
        current_results = {}

        # ファイル読み込み回帰テスト
        current_results["file_reading"] = self._benchmark_file_reading()

        # パース回帰テスト
        current_results["parsing"] = self._benchmark_parsing()

        # レンダリング回帰テスト
        current_results["rendering"] = self._benchmark_rendering()

        # 回帰分析
        regression_analysis = self._analyze_regression(current_results)
        self.logger.info(
            f"回帰テスト完了: {len(regression_analysis.get('regressions_detected', []))}個の回帰を検出"
        )

        return regression_analysis

    def save_baseline(self, output_file: Path):
        """現在の結果をベースラインとして保存

        Args:
            output_file: 保存先ファイル
        """
        if not self.results:
            self.logger.warning("保存するベンチマーク結果がありません")
            print("⚠️  No results to save as baseline")
            return

        baseline_data = {
            "timestamp": time.time(),
            "config": asdict(self.config),
            "results": {result.name: asdict(result) for result in self.results},
        }

        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(baseline_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"ベースライン保存完了: {output_file}")
            print(f"💾 Baseline saved to: {output_file}")
        except Exception as e:
            self.logger.error(f"ベースライン保存エラー: {e}")
            raise

    def load_baseline(self, baseline_file: Path):
        """ベースライン結果を読み込み

        Args:
            baseline_file: ベースラインファイル
        """
        try:
            with open(baseline_file, "r", encoding="utf-8") as f:
                baseline_data = json.load(f)

            self.baseline_results = {}
            for name, result_data in baseline_data["results"].items():
                self.baseline_results[name] = BenchmarkResult(**result_data)

            self.logger.info(
                f"ベースライン読み込み完了: {baseline_file}, {len(self.baseline_results)}個の結果"
            )
            print(f"📥 Baseline loaded from: {baseline_file}")

        except Exception as e:
            self.logger.error(f"ベースライン読み込みエラー: {e}")
            print(f"⚠️  Failed to load baseline: {e}")

    def _run_file_benchmarks(self):
        """ファイル読み込みベンチマーク"""
        # 小ファイル読み込み
        result = self._benchmark_file_reading(file_size="small")
        self.results.append(result)
        print(f"  Small files: {result.avg_time:.3f}s avg")

        # 大ファイル読み込み
        result = self._benchmark_file_reading(file_size="large")
        self.results.append(result)
        print(f"  Large files: {result.avg_time:.3f}s avg")

    def _run_parse_benchmarks(self):
        """パースベンチマーク"""
        # 基本パース
        result = self._benchmark_parsing(complexity="basic")
        self.results.append(result)
        print(f"  Basic parsing: {result.avg_time:.3f}s avg")

        # 複雑パース
        result = self._benchmark_parsing(complexity="complex")
        self.results.append(result)
        print(f"  Complex parsing: {result.avg_time:.3f}s avg")

    def _run_render_benchmarks(self):
        """レンダリングベンチマーク"""
        # 基本レンダリング
        result = self._benchmark_rendering(template="basic")
        self.results.append(result)
        print(f"  Basic rendering: {result.avg_time:.3f}s avg")

        # 複雑レンダリング
        result = self._benchmark_rendering(template="complex")
        self.results.append(result)
        print(f"  Complex rendering: {result.avg_time:.3f}s avg")

    def _run_e2e_benchmarks(self):
        """エンドツーエンドベンチマーク"""
        result = self._benchmark_full_pipeline()
        self.results.append(result)
        print(f"  Full pipeline: {result.avg_time:.3f}s avg")

    def _run_cache_benchmarks(self):
        """キャッシュパフォーマンステスト"""
        if not self.config.cache_enabled:
            print("  Cache disabled, skipping cache benchmarks")
            return

        # キャッシュヒット率テスト
        result = self._benchmark_cache_performance()
        self.results.append(result)
        print(f"  Cache performance: {result.avg_time:.3f}s avg")

    def _benchmark_file_reading(self, file_size: str = "medium") -> BenchmarkResult:
        """ファイル読み込みベンチマーク"""
        name = f"file_reading_{file_size}"

        # テストファイルを生成
        test_content = self._generate_test_content(file_size)
        test_file = Path(f"/tmp/benchmark_{file_size}.txt")
        test_file.write_text(test_content, encoding="utf-8")

        def benchmark_func():
            if self.file_cache:
                return self.file_cache.get_file_content(test_file)
            else:
                return test_file.read_text(encoding="utf-8")

        return self._run_benchmark(name, benchmark_func)

    def _benchmark_parsing(self, complexity: str = "basic") -> BenchmarkResult:
        """パースベンチマーク"""
        name = f"parsing_{complexity}"

        # テストコンテンツを生成
        test_content = self._generate_parse_test_content(complexity)

        def benchmark_func():
            if self.parse_cache:
                return self.parse_cache.get_parse_or_compute(
                    test_content, self._mock_parse_function
                )
            else:
                return self._mock_parse_function(test_content)

        return self._run_benchmark(name, benchmark_func)

    def _benchmark_rendering(self, template: str = "basic") -> BenchmarkResult:
        """レンダリングベンチマーク"""
        name = f"rendering_{template}"

        # テストデータを生成
        test_data = self._generate_render_test_data(template)
        content_hash = "test_hash"

        def benchmark_func():
            if self.render_cache:
                return self.render_cache.get_render_or_compute(
                    content_hash, template, self._mock_render_function, data=test_data
                )
            else:
                return self._mock_render_function(data=test_data)

        return self._run_benchmark(name, benchmark_func)

    def _benchmark_full_pipeline(self) -> BenchmarkResult:
        """フルパイプラインベンチマーク"""
        name = "full_pipeline"

        # テストファイルを準備
        test_content = self._generate_test_content("medium")
        test_file = Path("/tmp/benchmark_pipeline.txt")
        test_file.write_text(test_content, encoding="utf-8")

        def benchmark_func():
            # 1. ファイル読み込み
            if self.file_cache:
                content = self.file_cache.get_file_content(test_file)
            else:
                content = test_file.read_text(encoding="utf-8")

            # 2. パース
            if self.parse_cache:
                ast_nodes = self.parse_cache.get_parse_or_compute(
                    content, self._mock_parse_function
                )
            else:
                ast_nodes = self._mock_parse_function(content)

            # 3. レンダリング
            content_hash = "pipeline_hash"
            if self.render_cache:
                html = self.render_cache.get_render_or_compute(
                    content_hash,
                    "basic",
                    self._mock_render_function,
                    ast_nodes=ast_nodes,
                )
            else:
                html = self._mock_render_function(ast_nodes=ast_nodes)

            return html

        return self._run_benchmark(name, benchmark_func)

    def _benchmark_cache_performance(self) -> BenchmarkResult:
        """キャッシュパフォーマンステスト"""
        name = "cache_performance"

        # キャッシュを事前にウォームアップ
        test_content = self._generate_test_content("medium")

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

        def benchmark_func():
            # キャッシュヒットを期待
            if self.file_cache:
                self.file_cache.get_file_content(test_file)

            if self.parse_cache:
                self.parse_cache.get_parse_or_compute(
                    test_content, self._mock_parse_function
                )

            return "cached_result"

        return self._run_benchmark(name, benchmark_func)

    def _run_benchmark(self, name: str, func: Callable) -> BenchmarkResult:
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
                f"ベンチマーク {i+1}/{self.config.iterations}: {execution_time:.4f}s"
            )

        # プロファイリング終了
        if self.profiler:
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
        std_dev = statistics.stdev(times) if len(times) > 1 else 0

        # メモリ使用量
        memory_usage = {}
        if start_memory and end_memory:
            memory_usage = {
                "start_mb": start_memory.memory_mb,
                "end_mb": end_memory.memory_mb,
                "delta_mb": end_memory.memory_mb - start_memory.memory_mb,
                "peak_mb": max(start_memory.memory_mb, end_memory.memory_mb),
            }

        # キャッシュ統計
        cache_stats = {}
        if self.file_cache:
            cache_stats["file_cache"] = self.file_cache.get_cache_stats()
        if self.parse_cache:
            cache_stats["parse_cache"] = self.parse_cache.get_parse_statistics()
        if self.render_cache:
            cache_stats["render_cache"] = self.render_cache.get_render_statistics()

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
        )

        self.logger.info(
            f"ベンチマーク完了: {name}, 平均: {avg_time:.4f}s, "
            f"最小: {min_time:.4f}s, 最大: {max_time:.4f}s"
        )

        return result

    def _analyze_results(self) -> Dict[str, Any]:
        """結果を分析"""
        analysis = {
            "summary": {
                "total_benchmarks": len(self.results),
                "fastest_benchmark": (
                    min(self.results, key=lambda x: x.avg_time).name
                    if self.results
                    else None
                ),
                "slowest_benchmark": (
                    max(self.results, key=lambda x: x.avg_time).name
                    if self.results
                    else None
                ),
            },
            "detailed_results": [asdict(result) for result in self.results],
            "performance_insights": self._generate_performance_insights(),
        }

        # 回帰分析
        if self.baseline_results:
            analysis["regression_analysis"] = self._analyze_regression(
                {result.name: result for result in self.results}
            )

        return analysis

    def _analyze_regression(
        self, current_results: Dict[str, BenchmarkResult]
    ) -> Dict[str, Any]:
        """回帰分析を実行"""
        regression_analysis = {
            "regressions_detected": [],
            "improvements_detected": [],
            "stable_benchmarks": [],
        }

        threshold = 0.1  # 10%の変化を閾値とする

        for name, baseline in self.baseline_results.items():
            if name in current_results:
                current = current_results[name]

                # パフォーマンス変化を計算
                change_percent = (
                    (current.avg_time - baseline.avg_time) / baseline.avg_time
                ) * 100

                if change_percent > threshold * 100:
                    regression_analysis["regressions_detected"].append(
                        {
                            "benchmark": name,
                            "baseline_time": baseline.avg_time,
                            "current_time": current.avg_time,
                            "change_percent": change_percent,
                            "severity": (
                                "high"
                                if change_percent > 25
                                else "medium" if change_percent > 10 else "low"
                            ),
                        }
                    )
                elif change_percent < -threshold * 100:
                    regression_analysis["improvements_detected"].append(
                        {
                            "benchmark": name,
                            "baseline_time": baseline.avg_time,
                            "current_time": current.avg_time,
                            "change_percent": abs(change_percent),
                        }
                    )
                else:
                    regression_analysis["stable_benchmarks"].append(name)

        return regression_analysis

    def _generate_performance_insights(self) -> List[str]:
        """パフォーマンスインサイトを生成"""
        insights = []

        if not self.results:
            return insights

        # 平均時間の分析
        avg_times = [result.avg_time for result in self.results]
        overall_avg = statistics.mean(avg_times)

        if overall_avg > 1.0:
            insights.append(
                "全体的にパフォーマンスが遅い: 平均実行時間が1秒を超えています"
            )

        # キャッシュ効果の分析
        cache_results = [result for result in self.results if "cache" in result.name]
        if cache_results:
            cache_avg = statistics.mean([result.avg_time for result in cache_results])
            if cache_avg < overall_avg * 0.5:
                insights.append("キャッシュが効果的に動作しています")
            else:
                insights.append(
                    "キャッシュの効果が限定的です: 設定の見直しを検討してください"
                )

        # メモリ使用量の分析
        memory_results = [result for result in self.results if result.memory_usage]
        if memory_results:
            high_memory_results = [
                result
                for result in memory_results
                if result.memory_usage.get("delta_mb", 0) > 50
            ]
            if high_memory_results:
                insights.append(
                    f"{len(high_memory_results)}個のベンチマークで高いメモリ使用量が検出されました"
                )

        return insights

    def _generate_test_content(self, size: str) -> str:
        """テスト用コンテンツを生成"""
        base_content = """
# テストドキュメント

## 概要
これはパフォーマンステスト用のサンプルドキュメントです。

## 内容
- 項目1: 基本的な内容
- 項目2: より詳細な内容
- 項目3: 複雑な内容

### 詳細セクション
このセクションには詳細な説明が含まれています。
"""

        if size == "small":
            return base_content
        elif size == "medium":
            return base_content * 10
        elif size == "large":
            return base_content * 100
        else:
            return base_content

    def _generate_parse_test_content(self, complexity: str) -> str:
        """パーステスト用コンテンツを生成"""
        if complexity == "basic":
            return self._generate_test_content("small")
        else:
            return self._generate_test_content("large")

    def _generate_render_test_data(self, template: str) -> Dict[str, Any]:
        """レンダーテスト用データを生成"""
        if template == "basic":
            return {"title": "Test", "content": "Basic content"}
        else:
            return {
                "title": "Complex Test",
                "content": "Complex content" * 100,
                "items": [f"Item {i}" for i in range(100)],
            }

    def _mock_parse_function(self, content: str) -> List[Any]:
        """モックパース関数"""
        # 実際のパース処理をシミュレート
        time.sleep(0.001)  # 1ms のパース時間をシミュレート
        return [{"type": "text", "content": line} for line in content.split("\n")]

    def _mock_render_function(self, **kwargs) -> str:
        """モックレンダー関数"""
        # 実際のレンダリング処理をシミュレート
        time.sleep(0.002)  # 2ms のレンダリング時間をシミュレート
        return f"<html><body>{kwargs}</body></html>"
