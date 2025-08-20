"""
品質指標測定・評価モジュール

品質評価・安定性測定・エラー率・成功率計算・品質トレンド分析
統合品質評価・信頼性測定・品質基準判定システム
"""

import time
from typing import Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger

from ..measurement_core import MeasurementResult
from ..measurement_core import QualityMetrics as QualityMetricsData
from ..measurement_core import StabilityAssessment
from ..statistical_analyzer import StatisticalAnalyzer


class QualityMetrics:
    """品質指標測定・評価専用クラス

    品質評価・安定性測定・エラー率・成功率計算
    品質トレンド分析・統合品質評価・信頼性測定
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """品質測定システム初期化"""
        self.logger = get_logger(__name__)
        self.config = config or {}
        self.statistical_analyzer = StatisticalAnalyzer()

        # 品質測定用属性（エラー対応）
        self.timestamp: float = time.time()
        self.quality_score: float = 0.0

        # effect_measurement.py用の追加属性
        self.accuracy: float = 0.0
        self.precision: float = 0.0
        self.recall: float = 0.0
        self.response_time: float = 0.0
        self.throughput: float = 0.0
        self.error_rate: float = 0.0
        self.availability: float = 0.0

        # 品質測定基準
        self.quality_thresholds = self.config.get(
            "quality_thresholds",
            {
                "accuracy_minimum": 0.8,
                "stability_minimum": 0.9,
                "performance_minimum": 0.85,
                "reliability_minimum": 0.9,
                "response_time_maximum": 1.0,
                "error_rate_maximum": 0.05,
            },
        )

        # 品質履歴
        self.quality_history: List[QualityMetricsData] = []
        self.stability_assessments: List[StabilityAssessment] = []

    def measure_integrated_effects(
        self,
        system_metrics: Dict[str, float],
        baseline_measurement: Any,
        success_criteria: Dict[str, Any],
    ) -> MeasurementResult:
        """統合効果測定（Phase B + AI統合効果・相乗効果測定・総合68.8%削減確認）"""
        try:
            measurement_start = time.time()

            # 統合効果成分抽出
            phase_b_contribution = system_metrics.get("phase_b_efficiency", 66.8)
            ai_contribution = system_metrics.get("ai_efficiency_gain", 0.0)
            synergy_effect = system_metrics.get("synergy_effect", 0.0)

            # 総合効果計算
            total_integrated_effect = (
                phase_b_contribution + ai_contribution + synergy_effect
            )

            # ベースライン比較
            total_baseline = (
                baseline_measurement.get_baseline("total_efficiency") or 66.8
            )

            # 統合改善効果
            improvement, improvement_percentage = (
                self.statistical_analyzer.calculate_improvement(
                    total_baseline, total_integrated_effect
                )
            )

            # 目標達成評価
            target_achievement = (
                total_integrated_effect >= success_criteria["total_efficiency_target"]
            )

            # 相乗効果評価
            expected_simple_sum = phase_b_contribution + ai_contribution
            actual_synergy = total_integrated_effect - expected_simple_sum
            synergy_effectiveness = max(0.0, actual_synergy)

            # 統合品質評価
            integration_quality = self._assess_integration_quality(system_metrics)

            # 信頼度計算
            confidence_level = integration_quality * 0.7 + (
                0.3 if target_achievement else 0.0
            )

            # 統計的有意性
            statistical_significance = (
                target_achievement and improvement > 1.0
            )  # 1%以上改善

            # 測定結果構築
            integrated_measurement = MeasurementResult(
                measurement_type="integrated_effects",
                baseline_value=total_baseline,
                current_value=total_integrated_effect,
                improvement=improvement,
                improvement_percentage=improvement_percentage,
                measurement_time=time.time() - measurement_start,
                confidence_level=confidence_level,
                statistical_significance=statistical_significance,
                metadata={
                    "phase_b_contribution": phase_b_contribution,
                    "ai_contribution": ai_contribution,
                    "synergy_effect": synergy_effect,
                    "synergy_effectiveness": synergy_effectiveness,
                    "target_achievement": target_achievement,
                    "integration_quality": integration_quality,
                    "measurement_timestamp": time.time(),
                },
            )

            status = "TARGET_ACHIEVED" if target_achievement else "IN_PROGRESS"
            self.logger.info(
                f"Integrated effects measured: {total_integrated_effect:.3f}% - {status}"
            )

            return integrated_measurement
        except Exception as e:
            self.logger.error(f"Integrated effects measurement failed: {e}")
            return MeasurementResult(
                measurement_type="integrated_effects",
                baseline_value=66.8,
                current_value=66.8,
                improvement=0.0,
                improvement_percentage=0.0,
                measurement_time=0.0,
                confidence_level=0.5,
                statistical_significance=False,
                metadata={"error": str(e)},
            )

    def _assess_integration_quality(self, system_metrics: Dict[str, float]) -> float:
        """統合品質評価"""
        try:
            # 品質指標抽出
            accuracy = system_metrics.get("accuracy", 0.8)
            stability = system_metrics.get("stability", 0.9)
            performance = system_metrics.get("performance", 0.85)
            reliability = system_metrics.get("reliability", 0.9)

            # 統合品質スコア計算（重み付き平均）
            quality_score = (
                accuracy * 0.3 + stability * 0.3 + performance * 0.2 + reliability * 0.2
            )

            return min(1.0, max(0.0, quality_score))
        except Exception as e:
            self.logger.error(f"Integration quality assessment failed: {e}")
            return 0.5

    def _calculate_quality_metrics(
        self, system_metrics: Dict[str, float]
    ) -> QualityMetricsData:
        """品質指標計算"""
        try:
            # 品質指標抽出
            accuracy = system_metrics.get("accuracy", 0.8)
            precision = system_metrics.get("precision", 0.85)
            recall = system_metrics.get("recall", 0.82)
            response_time = system_metrics.get("response_time", 0.5)
            throughput = system_metrics.get("throughput", 100.0)
            error_rate = system_metrics.get("error_rate", 0.02)
            availability = system_metrics.get("availability", 0.99)

            # 品質評価
            quality_score = (accuracy + precision + recall) / 3

            quality_metrics = QualityMetricsData(
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                response_time=response_time,
                throughput=throughput,
                error_rate=error_rate,
                availability=availability,
                consistency=0.0,  # デフォルト値
                quality_score=quality_score,
                timestamp=time.time(),
            )

            # 履歴更新
            self.quality_history.append(quality_metrics)
            if len(self.quality_history) > 100:
                self.quality_history = self.quality_history[-100:]

            return quality_metrics
        except Exception as e:
            self.logger.error(f"Quality metrics calculation failed: {e}")
            return QualityMetricsData(
                accuracy=0.0,
                precision=0.0,
                recall=0.0,
                response_time=float("inf"),
                throughput=0.0,
                error_rate=1.0,
                availability=0.0,
                consistency=0.0,  # 必須フィールド
                quality_score=0.0,
                timestamp=time.time(),
            )

    def _calculate_stability_score(
        self, system_metrics: Dict[str, float]
    ) -> StabilityAssessment:
        """安定性スコア計算"""
        try:
            # 安定性指標抽出
            consistency = system_metrics.get("consistency", 0.9)
            predictability = system_metrics.get("predictability", 0.85)
            variance = system_metrics.get("variance", 0.1)
            drift_detection = system_metrics.get("drift_detection", 0.95)

            # 安定性評価
            consistency_score = consistency
            predictability_score = predictability
            variance_score = max(0.0, 1.0 - variance)  # 低分散ほど高スコア
            drift_score = drift_detection

            # 総合安定性スコア
            overall_stability = (
                consistency_score * 0.3
                + predictability_score * 0.3
                + variance_score * 0.2
                + drift_score * 0.2
            )

            # 安定性レベル判定
            if overall_stability >= 0.9:
                stability_level = "excellent"
            elif overall_stability >= 0.8:
                stability_level = "good"
            elif overall_stability >= 0.7:
                stability_level = "acceptable"
            else:
                stability_level = "poor"

            stability_assessment = StabilityAssessment(
                consistency_score=consistency_score,
                predictability_score=predictability_score,
                variance_score=variance_score,
                drift_score=drift_score,
                overall_stability=overall_stability,
                stability_level=stability_level,
                timestamp=time.time(),
            )

            # 履歴更新
            self.stability_assessments.append(stability_assessment)
            if len(self.stability_assessments) > 100:
                self.stability_assessments = self.stability_assessments[-100:]

            return stability_assessment
        except Exception as e:
            self.logger.error(f"Stability score calculation failed: {e}")
            return StabilityAssessment(
                consistency_score=0.0,
                predictability_score=0.0,
                variance_score=0.0,
                drift_score=0.0,
                overall_stability=0.0,
                stability_level="error",
                timestamp=time.time(),
            )

    def evaluate_quality(self, results: Any) -> Dict[str, Any]:
        """品質評価実行"""
        try:
            if not isinstance(results, dict):
                return {"error": "Invalid results format"}

            # 基本品質指標
            accuracy = results.get("accuracy", 0.0)
            error_rate = results.get("error_rate", 0.0)
            response_time = results.get("response_time", float("inf"))
            stability = results.get("stability", 0.0)

            # 品質判定
            quality_passed = (
                accuracy >= self.quality_thresholds["accuracy_minimum"]
                and error_rate <= self.quality_thresholds["error_rate_maximum"]
                and response_time <= self.quality_thresholds["response_time_maximum"]
                and stability >= self.quality_thresholds["stability_minimum"]
            )

            # 品質スコア計算
            accuracy_score = min(
                1.0, accuracy / self.quality_thresholds["accuracy_minimum"]
            )
            error_score = max(
                0.0, 1.0 - error_rate / self.quality_thresholds["error_rate_maximum"]
            )
            response_score = (
                max(
                    0.0,
                    self.quality_thresholds["response_time_maximum"] / response_time,
                )
                if response_time > 0
                else 0
            )
            stability_score = min(
                1.0, stability / self.quality_thresholds["stability_minimum"]
            )

            overall_quality = (
                accuracy_score + error_score + response_score + stability_score
            ) / 4

            return {
                "quality_passed": quality_passed,
                "overall_quality": overall_quality,
                "accuracy_score": accuracy_score,
                "error_score": error_score,
                "response_score": response_score,
                "stability_score": stability_score,
                "quality_rating": (
                    "high"
                    if overall_quality > 0.8
                    else "medium" if overall_quality > 0.6 else "low"
                ),
                "evaluation_timestamp": time.time(),
            }
        except Exception as e:
            self.logger.error(f"Quality evaluation failed: {e}")
            return {"error": str(e)}

    def analyze_quality_trend(self, days: int = 7) -> Dict[str, Any]:
        """品質トレンド分析"""
        try:
            if len(self.quality_history) < 2:
                return {"error": "Insufficient quality history for trend analysis"}

            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 3600)

            # 期間内データ抽出
            relevant_quality = [
                qm for qm in self.quality_history if qm.timestamp >= cutoff_time
            ]

            if len(relevant_quality) < 2:
                return {"error": "Insufficient data for trend analysis"}

            # トレンド計算
            quality_scores = [qm.quality_score for qm in relevant_quality]
            first_score = quality_scores[0]
            last_score = quality_scores[-1]
            trend_direction = (
                "improving"
                if last_score > first_score
                else "declining" if last_score < first_score else "stable"
            )

            # 統計
            avg_quality = sum(quality_scores) / len(quality_scores)
            min_quality = min(quality_scores)
            max_quality = max(quality_scores)

            return {
                "trend_direction": trend_direction,
                "quality_change": last_score - first_score,
                "average_quality": avg_quality,
                "min_quality": min_quality,
                "max_quality": max_quality,
                "data_points": len(relevant_quality),
                "analysis_period_days": days,
                "analysis_timestamp": current_time,
            }
        except Exception as e:
            self.logger.error(f"Quality trend analysis failed: {e}")
            return {"error": str(e)}
