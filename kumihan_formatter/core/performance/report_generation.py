"""
最適化レポート生成 - 分析結果出力・推奨事項作成
最適化結果の分析とレポート生成
Issue #476対応 - ファイルサイズ制限遵守
"""

import statistics
from typing import Any

from .optimization_types import REGRESSION_THRESHOLDS, OptimizationMetrics


class ReportGenerator:
    """最適化レポート生成

    機能:
    - 回帰検出
    - 推奨事項の生成
    - パフォーマンス分析レポート作成
    """

    def detect_regressions(self, metrics: list[OptimizationMetrics]) -> list[str]:
        """回帰を検出

        Args:
            metrics: 最適化メトリクスのリスト

        Returns:
            回帰警告のリスト
        """
        warnings = []

        for metric in metrics:
            if not metric.is_improvement:
                improvement_percent = metric.improvement_percent

                # 回帰の重大度を判定
                severity = None
                for level, threshold in REGRESSION_THRESHOLDS.items():
                    if improvement_percent <= threshold:
                        severity = level
                        break

                if severity:
                    severity_jp = {
                        "severe": "重大",
                        "moderate": "中程度",
                        "minor": "軽微",
                    }.get(severity, "不明")

                    warnings.append(
                        f"{severity_jp}な回帰: {metric.name} が "
                        f"{abs(improvement_percent):.1f}% 劣化"
                    )

        return warnings

    def generate_recommendations(self, metrics: list[OptimizationMetrics]) -> list[str]:
        """推奨事項を生成

        Args:
            metrics: 最適化メトリクスのリスト

        Returns:
            推奨事項のリスト
        """
        recommendations = []

        # パフォーマンス改善の推奨
        perf_metrics = [m for m in metrics if m.category == "performance"]
        if perf_metrics:
            improved_perf = [m for m in perf_metrics if m.is_improvement]
            if improved_perf:
                avg_improvement = statistics.mean(
                    [m.improvement_percent for m in improved_perf]
                )
                if avg_improvement > 20:
                    recommendations.append(
                        "キャッシュ最適化が非常に効果的です。"
                        "同様の戦略を他の処理にも適用することを検討してください。"
                    )
                elif avg_improvement > 10:
                    recommendations.append(
                        "パフォーマンス改善が確認されました。"
                        "さらなる最適化の余地があります。"
                    )

        # メモリ使用量の推奨
        memory_metrics = [m for m in metrics if m.category == "memory"]
        memory_improvements = [m for m in memory_metrics if m.is_improvement]
        if memory_metrics and len(memory_improvements) > len(memory_metrics) * 0.7:
            recommendations.append(
                "メモリ使用量が効果的に削減されています。"
                "メモリ監視を継続することを推奨します。"
            )

        return recommendations
