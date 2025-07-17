"""
最適化効果分析システム統合 - 分割されたコンポーネントの統合
分割された最適化分析コンポーネントを統合し、
元のOptimizationAnalyzerクラスと同等の機能を提供
Issue #476対応 - ファイルサイズ制限遵守
"""

import json
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..utilities.logger import get_logger
from .optimization_comparison import OptimizationComparisonEngine
from .optimization_measurement import OptimizationMeasurementSystem
from .optimization_types import OptimizationReport


class OptimizationAnalyzer:
    """最適化効果分析システム統合
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
        self.logger = get_logger(__name__)
        self.baseline_dir = baseline_dir or Path("./performance_baselines")
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        # コンポーネント初期化
        self.measurement_system = OptimizationMeasurementSystem(self.baseline_dir)
        self.comparison_engine = OptimizationComparisonEngine()
        # データ保存
        self.optimization_history: list[OptimizationReport] = []

    def capture_baseline(self, name: str, description: str = "") -> dict[str, Any]:
        """最適化前のベースライン性能を記録
        Args:
            name: ベースライン名
            description: 説明
        Returns:
            ベースラインデータ
        """
        return self.measurement_system.capture_baseline(name, description)

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
        self.logger.info(f"最適化効果測定開始: {optimization_name}")
        # ベースラインデータを読み込み
        baseline_data = self.measurement_system.load_baseline(baseline_name)
        if not baseline_data:
            raise ValueError(f"Baseline '{baseline_name}' not found")
        # 最適化後のベンチマークを実行
        optimized_results = self.measurement_system.measure_optimized_performance(
            optimization_name
        )
        # 比較分析
        metrics = self.comparison_engine.compare_performance(
            baseline_data["benchmark_results"], optimized_results
        )
        # レポート生成
        report = OptimizationReport(
            timestamp=datetime.now().isoformat(),
            optimization_name=optimization_name,
            total_improvement_score=self.comparison_engine.calculate_total_improvement_score(
                metrics
            ),
            metrics=metrics,
            performance_summary=self.comparison_engine.create_performance_summary(
                metrics
            ),
            recommendations=self.comparison_engine.generate_recommendations(metrics),
            regression_warnings=self.comparison_engine.detect_regressions(metrics),
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
        self.logger.info(f"最適化レポート保存完了: {report_file}")
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
                    f"  Total Cache Metrics: {cache_eff.get('total_cache_metrics', 0)}",
                    f"  Cache Improvements: {cache_eff.get('cache_improvements', 0)}",
                    f"  Avg Cache Improvement: {cache_eff.get('avg_cache_improvement', 0):.1f}%",
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

    # データ管理メソッド
    def list_baselines(self) -> list[str]:
        """利用可能なベースライン一覧を取得"""
        return self.measurement_system.list_baselines()

    def validate_baseline_consistency(self, baseline_name: str) -> dict[str, Any]:
        """ベースラインデータの一貫性を検証"""
        return self.measurement_system.validate_baseline_consistency(baseline_name)

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
            "baseline_data": self.measurement_system.baseline_data,
        }
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        print(f"📤 Optimization summary exported to: {output_file}")
