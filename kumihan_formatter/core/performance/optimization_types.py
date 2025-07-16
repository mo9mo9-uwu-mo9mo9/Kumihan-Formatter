"""
最適化データ型定義 - 最適化メトリクスと結果型

最適化効果測定のためのデータクラス定義
Issue #476対応 - ファイルサイズ制限遵守
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


# 最適化カテゴリの定数
OPTIMIZATION_CATEGORIES = {
    "performance": "実行時間性能",
    "memory": "メモリ使用量",
    "cache": "キャッシュ効果",
    "throughput": "スループット",
    "latency": "レイテンシ",
}

# 有意性判定の閾値
SIGNIFICANCE_THRESHOLDS = {
    "critical": 25.0,  # 25%以上の改善
    "high": 10.0,  # 10%以上の改善
    "medium": 5.0,  # 5%以上の改善
    "low": 1.0,  # 1%以上の改善
}

# 回帰検出の閾値
REGRESSION_THRESHOLDS = {
    "severe": -15.0,  # 15%以上の劣化
    "moderate": -10.0,  # 10%以上の劣化
    "minor": -5.0,  # 5%以上の劣化
}

# 改善スコアの重み
SCORE_WEIGHTS = {
    "critical": 4.0,
    "high": 3.0,
    "medium": 2.0,
    "low": 1.0,
}
