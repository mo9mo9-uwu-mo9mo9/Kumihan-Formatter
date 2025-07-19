"""
最適化比較システム - パフォーマンス比較とメトリクス計算
ベースラインと最適化後のパフォーマンスを比較しメトリクスを計算
Issue #476対応 - ファイルサイズ制限遵守

分割後の統合インターフェース:
- comparison_logic.py: 比較・計算ロジック
- data_processing.py: データ処理・要約
- report_generation.py: レポート生成・推奨事項
"""

from typing import Any

from .comparison_logic import ComparisonLogic
from .data_processing import DataProcessor
from .optimization_types import OptimizationMetrics
from .report_generation import ReportGenerator


class OptimizationComparisonEngine:
    """最適化比較エンジン（統合インターフェース）

    機能:
    - ベースラインと最適化後のパフォーマンス比較
    - 改善メトリクスの計算
    - 統計的有意性の評価
    - 回帰リスクの検出
    """

    def __init__(self) -> None:
        """比較エンジンを初期化"""
        self.comparison_logic = ComparisonLogic()
        self.data_processor = DataProcessor()
        self.report_generator = ReportGenerator()

    def compare_performance(
        self, baseline_results: dict[str, Any], optimized_results: dict[str, Any]
    ) -> list[OptimizationMetrics]:
        """パフォーマンスを比較"""
        return self.comparison_logic.compare_performance(
            baseline_results, optimized_results
        )

    def calculate_significance(self, improvement_percent: float) -> str:
        """改善の有意性を計算"""
        return self.comparison_logic.calculate_significance(improvement_percent)

    def calculate_total_improvement_score(
        self, metrics: list[OptimizationMetrics]
    ) -> float:
        """総合改善スコアを計算"""
        return self.comparison_logic.calculate_total_improvement_score(metrics)

    def create_performance_summary(
        self, metrics: list[OptimizationMetrics]
    ) -> dict[str, Any]:
        """パフォーマンス要約を作成"""
        return self.data_processor.create_performance_summary(metrics)

    def detect_regressions(self, metrics: list[OptimizationMetrics]) -> list[str]:
        """回帰を検出"""
        return self.report_generator.detect_regressions(metrics)

    def generate_recommendations(self, metrics: list[OptimizationMetrics]) -> list[str]:
        """推奨事項を生成"""
        return self.report_generator.generate_recommendations(metrics)
