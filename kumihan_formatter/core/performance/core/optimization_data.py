"""最適化関連のデータクラス

Single Responsibility Principle適用: 最適化メトリクス構造
Issue #476 Phase2対応 - パフォーマンスモジュール統合（クラス数制限対応）
"""

from dataclasses import dataclass
from typing import Any, Dict, List


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

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "name": self.name,
            "before_value": self.before_value,
            "after_value": self.after_value,
            "improvement_percent": self.improvement_percent,
            "improvement_absolute": self.improvement_absolute,
            "significance": self.significance,
            "category": self.category,
            "is_improvement": self.is_improvement,
        }


@dataclass
class OptimizationReport:
    """最適化レポート"""

    timestamp: str
    optimization_name: str
    total_improvement_score: float
    metrics: List[OptimizationMetrics]
    performance_summary: Dict[str, Any]
    recommendations: List[str]
    regression_warnings: List[str]

    def get_metrics_by_category(self, category: str) -> List[OptimizationMetrics]:
        """カテゴリ別メトリクスを取得"""
        return [m for m in self.metrics if m.category == category]

    def get_significant_improvements(self) -> List[OptimizationMetrics]:
        """重要な改善を取得"""
        return [
            m
            for m in self.metrics
            if m.significance in ["high", "critical"] and m.is_improvement
        ]

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "timestamp": self.timestamp,
            "optimization_name": self.optimization_name,
            "total_improvement_score": self.total_improvement_score,
            "metrics": [m.to_dict() for m in self.metrics],
            "performance_summary": self.performance_summary,
            "recommendations": self.recommendations,
            "regression_warnings": self.regression_warnings,
        }
