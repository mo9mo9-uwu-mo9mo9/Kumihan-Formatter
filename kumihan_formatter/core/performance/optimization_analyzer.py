"""
最適化効果分析ツール - パフォーマンス改善の定量的評価

キャッシュ最適化とパフォーマンス向上の効果を測定・分析
Issue #402対応 - パフォーマンス最適化
"""

import json
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..performance import get_global_monitor
from .benchmark import BenchmarkConfig, PerformanceBenchmarkSuite
from .memory_monitor import MemoryMonitor
from .profiler import AdvancedProfiler


@dataclass
class OptimizationMetrics:
    """最適化メトリクス"""

    name: str
    before_value: float
    after_value: float
    improvement_percent: float
    improvement_absolute: float
    significance: str  # low, medium, high, critical
    category: str  # performance, memory, cache, etc.

    @property
    def is_improvement(self) -> bool:
        """改善があったかどうか"""
        return self.improvement_percent > 0


@dataclass
class OptimizationReport:
    """最適化レポート"""

    timestamp: str
    optimization_name: str
    total_improvement_score: float
    metrics: list[OptimizationMetrics]
    performance_summary: dict[str, Any]
    recommendations: list[str]
    regression_warnings: list[str]

    def get_metrics_by_category(self, category: str) -> list[OptimizationMetrics]:
        """カテゴリ別メトリクスを取得"""
        return [m for m in self.metrics if m.category == category]

    def get_significant_improvements(self) -> list[OptimizationMetrics]:
        """重要な改善を取得"""
        return [
            m
            for m in self.metrics
            if m.significance in ["high", "critical"] and m.is_improvement
        ]


class OptimizationAnalyzer:
    """最適化効果分析システム

    機能:
    - Before/After パフォーマンス比較
    - 統計的有意性検定
    - 改善効果の定量的評価
    - 回帰リスクの評価
    - 最適化レポート生成
    """

    def __init__(self, baseline_dir: Path = None):  # type: ignore
        """最適化分析器を初期化

        Args:
            baseline_dir: ベースラインデータの保存ディレクトリ
        """
        self.baseline_dir = baseline_dir or Path("./performance_baselines")
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

        # 測定ツール
        self.monitor = get_global_monitor()
        self.profiler = AdvancedProfiler()
        self.memory_monitor = MemoryMonitor()

        # データ保存
        self.baseline_data: dict[str, Any] = {}
        self.optimization_history: list[OptimizationReport] = []

    def capture_baseline(self, name: str, description: str = "") -> dict[str, Any]:
        """最適化前のベースライン性能を記録

        Args:
            name: ベースライン名
            description: 説明

        Returns:
            ベースラインデータ
        """
        print(f"📊 Capturing baseline: {name}")

        # ベンチマークスイートを実行
        benchmark_config = BenchmarkConfig(
            iterations=5,
            warmup_iterations=2,
            enable_profiling=True,
            enable_memory_monitoring=True,
            cache_enabled=False,  # 最適化前はキャッシュを無効
        )

        benchmark_suite = PerformanceBenchmarkSuite(benchmark_config)
        baseline_results = benchmark_suite.run_full_benchmark_suite()

        # ベースラインデータを構築
        baseline_data = {
            "name": name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "benchmark_results": baseline_results,
            "system_info": self._capture_system_info(),
        }

        # 保存
        self.baseline_data[name] = baseline_data
        baseline_file = self.baseline_dir / f"{name}_baseline.json"
        with open(baseline_file, "w", encoding="utf-8") as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Baseline captured and saved to: {baseline_file}")
        return baseline_data

    def measure_optimization_impact(
        self,
        optimization_name: str,
        baseline_name: str,
        description: str = "",
    ) -> OptimizationReport:
        """最適化後の効果を測定

        Args:
            optimization_name: 最適化名
            baseline_name: 比較対象のベースライン名
            description: 最適化の説明

        Returns:
            最適化レポート
        """
        print(f"🔍 Measuring optimization impact: {optimization_name}")

        # ベースラインデータを読み込み
        baseline_data = self._load_baseline(baseline_name)
        if not baseline_data:
            raise ValueError(f"Baseline '{baseline_name}' not found")

        # 最適化後のベンチマークを実行
        benchmark_config = BenchmarkConfig(
            iterations=5,
            warmup_iterations=2,
            enable_profiling=True,
            enable_memory_monitoring=True,
            cache_enabled=True,  # 最適化後はキャッシュを有効
        )

        benchmark_suite = PerformanceBenchmarkSuite(benchmark_config)
        optimized_results = benchmark_suite.run_full_benchmark_suite()

        # 比較分析
        metrics = self._compare_performance(
            baseline_data["benchmark_results"], optimized_results
        )

        # レポート生成
        report = OptimizationReport(
            timestamp=datetime.now().isoformat(),
            optimization_name=optimization_name,
            total_improvement_score=self._calculate_total_improvement_score(metrics),
            metrics=metrics,
            performance_summary=self._create_performance_summary(metrics),
            recommendations=self._generate_recommendations(metrics),
            regression_warnings=self._detect_regressions(metrics),
        )

        # 履歴に保存
        self.optimization_history.append(report)

        # ファイルに保存
        report_file = (
            self.baseline_dir / f"{optimization_name}_optimization_report.json"
        )
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)

        print(f"📈 Optimization report saved to: {report_file}")
        return report

    def generate_comprehensive_report(self, optimization_name: str) -> str:
        """包括的な最適化レポートを生成

        Args:
            optimization_name: 最適化名

        Returns:
            フォーマットされたレポート文字列
        """
        # 対応するレポートを検索
        report = None
        for r in self.optimization_history:
            if r.optimization_name == optimization_name:
                report = r
                break

        if not report:
            return f"Optimization report for '{optimization_name}' not found."

        lines = [
            f"🚀 Optimization Impact Report: {optimization_name}",
            "=" * 80,
            f"Generated: {report.timestamp}",
            f"Total Improvement Score: {report.total_improvement_score:.2f}",
            "",
        ]

        # 主要改善点
        significant_improvements = report.get_significant_improvements()
        if significant_improvements:
            lines.extend(
                [
                    "📈 Significant Improvements:",
                    "-" * 40,
                ]
            )
            for metric in significant_improvements:
                lines.append(
                    f"  ✅ {metric.name}: {metric.improvement_percent:.1f}% improvement "
                    f"({metric.before_value:.3f}s → {metric.after_value:.3f}s)"
                )
            lines.append("")

        # カテゴリ別分析
        categories = ["performance", "memory", "cache"]
        for category in categories:
            category_metrics = report.get_metrics_by_category(category)
            if category_metrics:
                lines.extend(
                    [
                        f"📊 {category.title()} Metrics:",
                        "-" * 25,
                    ]
                )
                for metric in category_metrics:
                    status = "✅" if metric.is_improvement else "⚠️"
                    lines.append(
                        f"  {status} {metric.name}: {metric.improvement_percent:+.1f}% "
                        f"({metric.significance} significance)"
                    )
                lines.append("")

        # 推奨事項
        if report.recommendations:
            lines.extend(
                [
                    "💡 Recommendations:",
                    "-" * 20,
                ]
            )
            for rec in report.recommendations:
                lines.append(f"  • {rec}")
            lines.append("")

        # 回帰警告
        if report.regression_warnings:
            lines.extend(
                [
                    "⚠️  Regression Warnings:",
                    "-" * 25,
                ]
            )
            for warning in report.regression_warnings:
                lines.append(f"  ⚠️  {warning}")
            lines.append("")

        # パフォーマンス要約
        summary = report.performance_summary
        lines.extend(
            [
                "📋 Performance Summary:",
                "-" * 25,
                f"  Total Benchmarks: {summary.get('total_benchmarks', 0)}",
                f"  Improved Metrics: {summary.get('improved_metrics', 0)}",
                f"  Degraded Metrics: {summary.get('degraded_metrics', 0)}",
                f"  Stable Metrics: {summary.get('stable_metrics', 0)}",
            ]
        )

        if summary.get("cache_effectiveness"):
            cache_eff = summary["cache_effectiveness"]
            lines.extend(
                [
                    "",
                    "💾 Cache Effectiveness:",
                    "-" * 22,
                    f"  File Cache Hit Rate: {cache_eff.get('file_cache_hit_rate', 0):.1%}",
                    f"  Parse Cache Hit Rate: {cache_eff.get('parse_cache_hit_rate', 0):.1%}",
                    f"  Render Cache Hit Rate: {cache_eff.get('render_cache_hit_rate', 0):.1%}",
                ]
            )

        return "\n".join(lines)

    def compare_optimizations(self, optimization_names: list[str]) -> dict[str, Any]:
        """複数の最適化を比較

        Args:
            optimization_names: 比較する最適化名のリスト

        Returns:
            比較結果
        """
        comparison_data = {  # type: ignore
            "optimizations": {},
            "ranking": [],
            "best_practices": [],
        }

        reports = []
        for name in optimization_names:
            for report in self.optimization_history:
                if report.optimization_name == name:
                    reports.append(report)
                    break

        if not reports:
            return {"error": "No optimization reports found for comparison"}

        # 各最適化のスコアを比較
        for report in reports:
            comparison_data["optimizations"][report.optimization_name] = {  # type: ignore
                "total_score": report.total_improvement_score,
                "significant_improvements": len(report.get_significant_improvements()),
                "regression_warnings": len(report.regression_warnings),
            }

        # ランキング作成
        ranking = sorted(
            comparison_data["optimizations"].items(),  # type: ignore
            key=lambda x: x[1]["total_score"],
            reverse=True,
        )
        comparison_data["ranking"] = [name for name, _ in ranking]

        # ベストプラクティス抽出
        best_practices = set()
        for report in reports:
            if report.total_improvement_score > 10:  # 高スコアの最適化から
                for rec in report.recommendations[:2]:  # 上位2つの推奨事項
                    best_practices.add(rec)

        comparison_data["best_practices"] = list(best_practices)

        return comparison_data

    def _load_baseline(self, baseline_name: str) -> dict[str, Any] | None:
        """ベースラインデータを読み込み"""
        if baseline_name in self.baseline_data:
            return self.baseline_data[baseline_name]  # type: ignore

        baseline_file = self.baseline_dir / f"{baseline_name}_baseline.json"
        if baseline_file.exists():
            with open(baseline_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.baseline_data[baseline_name] = data
                return data  # type: ignore

        return None

    def _compare_performance(
        self, baseline_results: dict[str, Any], optimized_results: dict[str, Any]
    ) -> list[OptimizationMetrics]:
        """パフォーマンスを比較"""
        metrics = []

        # 詳細結果から比較
        baseline_detailed = baseline_results.get("detailed_results", [])
        optimized_detailed = optimized_results.get("detailed_results", [])

        # ベンチマーク名でマッピング
        baseline_map = {result["name"]: result for result in baseline_detailed}
        optimized_map = {result["name"]: result for result in optimized_detailed}

        # 共通のベンチマークを比較
        for name in set(baseline_map.keys()) & set(optimized_map.keys()):
            baseline_result = baseline_map[name]
            optimized_result = optimized_map[name]

            # 実行時間の比較
            before_time = baseline_result["avg_time"]
            after_time = optimized_result["avg_time"]

            if before_time > 0:
                improvement_percent = ((before_time - after_time) / before_time) * 100
                improvement_absolute = before_time - after_time

                metrics.append(
                    OptimizationMetrics(
                        name=f"{name}_execution_time",
                        before_value=before_time,
                        after_value=after_time,
                        improvement_percent=improvement_percent,
                        improvement_absolute=improvement_absolute,
                        significance=self._calculate_significance(improvement_percent),
                        category="performance",
                    )
                )

            # メモリ使用量の比較（利用可能な場合）
            baseline_memory = baseline_result.get("memory_usage", {})
            optimized_memory = optimized_result.get("memory_usage", {})

            if baseline_memory and optimized_memory:
                before_memory = baseline_memory.get("peak_mb", 0)
                after_memory = optimized_memory.get("peak_mb", 0)

                if before_memory > 0:
                    memory_improvement = (
                        (before_memory - after_memory) / before_memory
                    ) * 100

                    metrics.append(
                        OptimizationMetrics(
                            name=f"{name}_memory_usage",
                            before_value=before_memory,
                            after_value=after_memory,
                            improvement_percent=memory_improvement,
                            improvement_absolute=before_memory - after_memory,
                            significance=self._calculate_significance(
                                memory_improvement
                            ),
                            category="memory",
                        )
                    )

        return metrics

    def _calculate_significance(self, improvement_percent: float) -> str:
        """改善の有意性を計算"""
        abs_improvement = abs(improvement_percent)

        if abs_improvement >= 25:
            return "critical"
        elif abs_improvement >= 10:
            return "high"
        elif abs_improvement >= 5:
            return "medium"
        else:
            return "low"

    def _calculate_total_improvement_score(
        self, metrics: list[OptimizationMetrics]
    ) -> float:
        """総合改善スコアを計算"""
        if not metrics:
            return 0.0

        total_score = 0.0
        weight_map = {
            "critical": 4.0,
            "high": 3.0,
            "medium": 2.0,
            "low": 1.0,
        }

        for metric in metrics:
            # 改善のみをスコアに含める
            if metric.is_improvement:
                weight = weight_map.get(metric.significance, 1.0)
                total_score += metric.improvement_percent * weight

        return total_score

    def _create_performance_summary(
        self, metrics: list[OptimizationMetrics]
    ) -> dict[str, Any]:
        """パフォーマンス要約を作成"""
        improved = [m for m in metrics if m.is_improvement]
        degraded = [
            m for m in metrics if not m.is_improvement and m.improvement_percent < -1
        ]
        stable = [m for m in metrics if -1 <= m.improvement_percent <= 1]

        summary = {
            "total_benchmarks": len(metrics),
            "improved_metrics": len(improved),
            "degraded_metrics": len(degraded),
            "stable_metrics": len(stable),
        }

        # キャッシュ効果の分析
        cache_metrics = [m for m in metrics if "cache" in m.name.lower()]
        if cache_metrics:
            cache_improvements = [m for m in cache_metrics if m.is_improvement]
            summary["cache_effectiveness"] = {  # type: ignore
                "total_cache_metrics": len(cache_metrics),
                "cache_improvements": len(cache_improvements),
                "avg_cache_improvement": (
                    statistics.mean([m.improvement_percent for m in cache_improvements])
                    if cache_improvements
                    else 0
                ),
            }

        return summary

    def _generate_recommendations(
        self, metrics: list[OptimizationMetrics]
    ) -> list[str]:
        """推奨事項を生成"""
        recommendations = []

        # パフォーマンス改善の推奨
        perf_metrics = [m for m in metrics if m.category == "performance"]
        if perf_metrics:
            avg_improvement = statistics.mean(
                [m.improvement_percent for m in perf_metrics if m.is_improvement]
            )
            if avg_improvement > 20:
                recommendations.append(
                    "キャッシュ最適化が非常に効果的です。同様の戦略を他の処理にも適用することを検討してください。"
                )
            elif avg_improvement > 10:
                recommendations.append(
                    "パフォーマンス改善が確認されました。さらなる最適化の余地があります。"
                )

        # メモリ使用量の推奨
        memory_metrics = [m for m in metrics if m.category == "memory"]
        memory_improvements = [m for m in memory_metrics if m.is_improvement]
        if len(memory_improvements) > len(memory_metrics) * 0.7:
            recommendations.append(
                "メモリ使用量が効果的に削減されています。メモリ監視を継続することを推奨します。"
            )

        # キャッシュ関連の推奨
        cache_metrics = [m for m in metrics if "cache" in m.name.lower()]
        if cache_metrics:
            cache_improvements = [m for m in cache_metrics if m.is_improvement]
            if len(cache_improvements) == len(cache_metrics):
                recommendations.append(
                    "キャッシュ戦略が全面的に効果的です。キャッシュサイズとTTL設定の最適化を検討してください。"
                )

        return recommendations

    def _detect_regressions(self, metrics: list[OptimizationMetrics]) -> list[str]:
        """回帰を検出"""
        warnings = []

        for metric in metrics:
            if (
                not metric.is_improvement and metric.improvement_percent < -5
            ):  # 5%以上の劣化
                severity = "重大" if metric.improvement_percent < -15 else "軽微"
                warnings.append(
                    f"{severity}な回帰: {metric.name} が {abs(metric.improvement_percent):.1f}% 劣化"
                )

        return warnings

    def _capture_system_info(self) -> dict[str, Any]:
        """システム情報を記録"""
        import platform
        import sys

        system_info: dict[str, Any] = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "cpu_count": None,
            "memory_total": None,
        }

        try:
            import psutil

            system_info["cpu_count"] = psutil.cpu_count()
            system_info["memory_total"] = psutil.virtual_memory().total
        except ImportError:
            pass

        return system_info

    def cleanup_old_data(self, days_old: int = 30):  # type: ignore
        """古いデータをクリーンアップ

        Args:
            days_old: 削除対象の日数
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)

        # 古いベースラインファイルを削除
        for baseline_file in self.baseline_dir.glob("*_baseline.json"):
            if baseline_file.stat().st_mtime < cutoff_date.timestamp():
                baseline_file.unlink()
                print(f"🗑️  Deleted old baseline: {baseline_file}")

        # 古いレポートファイルを削除
        for report_file in self.baseline_dir.glob("*_optimization_report.json"):
            if report_file.stat().st_mtime < cutoff_date.timestamp():
                report_file.unlink()
                print(f"🗑️  Deleted old report: {report_file}")

    def export_optimization_summary(self, output_file: Path):  # type: ignore
        """最適化の要約をエクスポート

        Args:
            output_file: 出力ファイルパス
        """
        summary_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_optimizations": len(self.optimization_history),
            "optimization_reports": [
                asdict(report) for report in self.optimization_history
            ],
            "baseline_data": self.baseline_data,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        print(f"📤 Optimization summary exported to: {output_file}")
