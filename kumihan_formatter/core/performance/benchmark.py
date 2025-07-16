"""
統合ベンチマークスイート - 分割されたコンポーネントの統合

分割されたベンチマークコンポーネントを統合し、
元のPerformanceBenchmarkSuiteクラスと同等の機能を提供
Issue #476対応 - ファイルサイズ制限遵守
"""

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..caching.file_cache import FileCache
from ..caching.parse_cache import ParseCache
from ..caching.render_cache import RenderCache
from ..performance import get_global_monitor
from ..utilities.logger import get_logger
from .benchmark_analyzer import BenchmarkAnalyzer
from .benchmark_runner import BenchmarkRunner
from .benchmark_types import BenchmarkConfig, BenchmarkResult, DEFAULT_BENCHMARK_CONFIG
from .memory_monitor import MemoryMonitor
from .profiler import AdvancedProfiler


class PerformanceBenchmarkSuite:
    """パフォーマンスベンチマーク総合スイート

    機能:
    - キャッシュあり/なしの性能比較
    - メモリ使用量の測定
    - プロファイリング統合
    - 回帰検出
    - ベースライン比較
    """

    def __init__(self, config: BenchmarkConfig | None = None) -> None:
        """ベンチマークスイートを初期化

        Args:
            config: ベンチマーク設定
        """
        self.logger = get_logger(__name__)
        self.config = config or DEFAULT_BENCHMARK_CONFIG
        self.logger.info(
            f"PerformanceBenchmarkSuite初期化: iterations={self.config.iterations}, "
            f"warmup={self.config.warmup_iterations}"
        )

        # パフォーマンス測定ツール
        self.monitor = get_global_monitor()
        self.profiler = AdvancedProfiler() if self.config.enable_profiling else None
        self.memory_monitor = (
            MemoryMonitor() if self.config.enable_memory_monitoring else None
        )

        self.logger.debug(
            f"profiling={self.config.enable_profiling}, "
            f"memory_monitoring={self.config.enable_memory_monitoring}"
        )

        # キャッシュシステム
        self.file_cache = FileCache() if self.config.cache_enabled else None
        self.parse_cache = ParseCache() if self.config.cache_enabled else None
        self.render_cache = RenderCache() if self.config.cache_enabled else None

        # コンポーネント初期化
        self.runner = BenchmarkRunner(
            self.config,
            self.file_cache,
            self.parse_cache,
            self.render_cache,
            self.memory_monitor,
            self.profiler,
        )
        self.analyzer = BenchmarkAnalyzer()

        # 結果保存
        self.results: list[BenchmarkResult] = []
        self.baseline_results: dict[str, BenchmarkResult] | None = None

        # ベースラインを読み込み
        if self.config.baseline_file and self.config.baseline_file.exists():
            self.load_baseline(self.config.baseline_file)

        self.logger.info("PerformanceBenchmarkSuite初期化完了")

    def run_full_benchmark_suite(self) -> dict[str, Any]:
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
            file_results = self.runner.run_file_benchmarks()
            self.results.extend(file_results)

            # 2. パースベンチマーク
            self.logger.info("パースベンチマーク開始")
            print("\n🔍 Parsing Benchmarks:")
            parse_results = self.runner.run_parse_benchmarks()
            self.results.extend(parse_results)

            # 3. レンダリングベンチマーク
            self.logger.info("レンダリングベンチマーク開始")
            print("\n🎨 Rendering Benchmarks:")
            render_results = self.runner.run_render_benchmarks()
            self.results.extend(render_results)

            # 4. 統合ベンチマーク
            self.logger.info("エンドツーエンドベンチマーク開始")
            print("\n🔄 End-to-End Benchmarks:")
            e2e_results = self.runner.run_e2e_benchmarks()
            self.results.extend(e2e_results)

            # 5. キャッシュパフォーマンステスト
            self.logger.info("キャッシュパフォーマンステスト開始")
            print("\n💾 Cache Performance Tests:")
            cache_results = self.runner.run_cache_benchmarks()
            self.results.extend(cache_results)

        finally:
            # メモリ監視停止
            if self.memory_monitor:
                self.memory_monitor.stop_monitoring()
                self.logger.debug("メモリ監視停止")

        # 結果分析
        analysis = self.analyzer.analyze_results(self.results)
        self.logger.info(
            f"ベンチマークスイート完了: {len(self.results)}個のベンチマークを実行"
        )

        print("\n📊 Benchmark Complete!")
        print("=" * 60)

        return analysis

    def run_regression_test(self) -> dict[str, Any]:
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
        current_results["file_reading_medium"] = self.runner.benchmark_file_reading()

        # パース回帰テスト
        current_results["parsing_basic"] = self.runner.benchmark_parsing()

        # レンダリング回帰テスト
        current_results["rendering_basic"] = self.runner.benchmark_rendering()

        # 回帰分析
        regression_analysis = self.analyzer.analyze_regression(
            current_results, self.baseline_results
        )
        self.logger.info(
            f"回帰テスト完了: {len(regression_analysis.get('regressions_detected', []))}個の回帰を検出"
        )

        return regression_analysis

    def save_baseline(self, output_file: Path) -> None:
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

    def load_baseline(self, baseline_file: Path) -> Any:
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

    def generate_report(self) -> dict[str, Any]:
        """包括的なベンチマークレポートを生成"""
        if not self.results:
            return {"error": "No benchmark results available"}

        # 基本分析
        analysis = self.analyzer.analyze_results(self.results)
        
        # サマリー生成
        summary = self.analyzer.generate_benchmark_summary(self.results)
        
        # 回帰分析（ベースラインがある場合）
        regression_analysis = None
        if self.baseline_results:
            current_results = {r.name: r for r in self.results}
            regression_analysis = self.analyzer.analyze_regression(
                current_results, self.baseline_results
            )

        report = {
            "summary": asdict(summary),
            "detailed_analysis": analysis,
            "regression_analysis": regression_analysis,
            "config": asdict(self.config),
            "timestamp": time.time(),
        }

        self.logger.info("ベンチマークレポート生成完了")
        return report

    def clear_results(self) -> None:
        """結果をクリア"""
        cleared_count = len(self.results)
        self.results.clear()
        self.logger.info(f"ベンチマーク結果をクリア: {cleared_count}個")

    # プロパティアクセス（後方互換性）
    @property
    def latest_results(self) -> list[BenchmarkResult]:
        """最新の結果リストへのアクセス"""
        return self.results

    @property
    def has_baseline(self) -> bool:
        """ベースラインが存在するかチェック"""
        return self.baseline_results is not None

    # 統計アクセス
    def get_performance_summary(self) -> dict[str, Any]:
        """パフォーマンスサマリーを取得"""
        if not self.results:
            return {"error": "No results available"}

        summary = self.analyzer.generate_benchmark_summary(self.results)
        return {
            "total_benchmarks": summary.total_benchmarks,
            "total_runtime": summary.total_runtime,
            "performance_score": summary.performance_score,
            "fastest_benchmark": {
                "name": summary.fastest_benchmark.name,
                "time": summary.fastest_benchmark.avg_time,
            },
            "slowest_benchmark": {
                "name": summary.slowest_benchmark.name,
                "time": summary.slowest_benchmark.avg_time,
            },
            "memory_peak_mb": summary.memory_peak,
            "cache_hit_rate": summary.cache_hit_rate,
        }