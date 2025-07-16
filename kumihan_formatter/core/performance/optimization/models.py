"""
最適化分析データモデル - Issue #402対応

最適化効果測定と分析のためのデータ構造。
"""

from dataclasses import dataclass
from typing import Any


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

    @property
    def is_regression(self) -> bool:
        """パフォーマンスが悪化したかどうか"""
        return self.improvement_percent < -5  # 5%以上の悪化

    @property
    def is_significant(self) -> bool:
        """統計的に有意な変化かどうか"""
        return self.significance in ["high", "critical"]


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

    def get_regressions(self) -> list[OptimizationMetrics]:
        """パフォーマンス悪化を取得"""
        return [m for m in self.metrics if m.is_regression]

    def get_improvement_summary(self) -> dict[str, Any]:
        """改善サマリーを取得"""
        improvements = [m for m in self.metrics if m.is_improvement]
        regressions = self.get_regressions()

        return {
            "total_metrics": len(self.metrics),
            "improvements_count": len(improvements),
            "regressions_count": len(regressions),
            "avg_improvement_percent": (
                sum(m.improvement_percent for m in improvements) / len(improvements)
                if improvements
                else 0
            ),
            "max_improvement_percent": (
                max(m.improvement_percent for m in improvements) if improvements else 0
            ),
            "significant_improvements": len(self.get_significant_improvements()),
        }

    def to_dict(self) -> dict[str, Any]:
        """辞書形式に変換"""
        return {
            "timestamp": self.timestamp,
            "optimization_name": self.optimization_name,
            "total_improvement_score": self.total_improvement_score,
            "metrics": [m.__dict__ for m in self.metrics],
            "performance_summary": self.performance_summary,
            "recommendations": self.recommendations,
            "regression_warnings": self.regression_warnings,
            "summary": self.get_improvement_summary(),
        }
