"""
パフォーマンス指標測定モジュール

AI効果・Phase B基盤・システムパフォーマンス測定専用クラス
処理時間・スループット・メモリ使用量・効率指標計算
"""

import time
from typing import Any, Dict, List, Optional, Tuple

from kumihan_formatter.core.utilities.logger import get_logger

from ..measurement_core import MeasurementResult
from ..statistical_analyzer import StatisticalAnalyzer


class PerformanceMetrics:
    """パフォーマンス指標測定専用クラス

    AI効果・Phase B基盤・システムパフォーマンス測定
    処理時間・スループット・メモリ使用量・効率指標計算
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """パフォーマンス測定システム初期化"""
        self.logger = get_logger(__name__)
        self.config = config or {}
        self.statistical_analyzer = StatisticalAnalyzer()

        # パフォーマンス測定設定
        self.success_criteria = self.config.get(
            "success_criteria",
            {
                "ai_contribution_target": 2.0,  # AI貢献度目標2.0%
                "phase_b_preservation_threshold": 66.0,  # Phase B保護基準66%
                "measurement_confidence_threshold": 0.8,  # 測定信頼度基準80%
            },
        )

        # 継続測定データ
        self.continuous_measurements: Dict[str, List[Tuple[float, float]]] = {}

    def measure_ai_contribution(
        self, current_ai_metrics: Dict[str, float]
    ) -> MeasurementResult:
        """AI専用削減効果測定（Phase B基盤効果分離）"""
        try:
            measurement_start = time.time()

            # AI効果抽出
            ai_efficiency_gain = current_ai_metrics.get("ai_efficiency_gain", 0.0)
            ai_optimization_impact = current_ai_metrics.get(
                "optimization_improvement", 0.0
            )
            ai_prediction_accuracy = current_ai_metrics.get("prediction_accuracy", 0.0)

            # AI貢献度計算（Phase B基盤から分離）
            ai_baseline = 0.0  # AI効果のベースライン（Phase B基盤なし）
            current_ai_effect = ai_efficiency_gain + ai_optimization_impact

            # 改善効果計算
            improvement, improvement_percentage = (
                self.statistical_analyzer.calculate_improvement(
                    ai_baseline, current_ai_effect
                )
            )

            # 信頼度評価
            confidence_level = min(
                1.0, ai_prediction_accuracy * 0.8 + 0.2
            )  # 予測精度ベース信頼度

            # 統計的有意性
            statistical_significance = current_ai_effect > 0.1  # 0.1%以上で有意

            # 測定結果構築
            ai_measurement = MeasurementResult(
                measurement_type="ai_contribution",
                baseline_value=ai_baseline,
                current_value=current_ai_effect,
                improvement=improvement,
                improvement_percentage=improvement_percentage,
                measurement_time=time.time() - measurement_start,
                confidence_level=confidence_level,
                statistical_significance=statistical_significance,
                metadata={
                    "ai_efficiency_gain": ai_efficiency_gain,
                    "optimization_impact": ai_optimization_impact,
                    "prediction_accuracy": ai_prediction_accuracy,
                    "measurement_timestamp": time.time(),
                },
            )

            # 継続測定データ更新
            self._update_continuous_measurement("ai_contribution", current_ai_effect)

            self.logger.info(
                f"AI contribution measured: {current_ai_effect:.3f}% (target: 2.0%)"
            )
            return ai_measurement
        except Exception as e:
            self.logger.error(f"AI contribution measurement failed: {e}")
            return MeasurementResult(
                measurement_type="ai_contribution",
                baseline_value=0.0,
                current_value=0.0,
                improvement=0.0,
                improvement_percentage=0.0,
                measurement_time=0.0,
                confidence_level=0.0,
                statistical_significance=False,
                metadata={"error": str(e)},
            )

    def validate_phase_b_preservation(
        self, current_system_metrics: Dict[str, float], baseline_measurement: Any
    ) -> MeasurementResult:
        """Phase B基盤（66.8%削減）維持確認"""
        try:
            measurement_start = time.time()

            # Phase B基盤効果測定
            phase_b_efficiency = current_system_metrics.get("phase_b_efficiency", 0.0)
            settings_manager_performance = current_system_metrics.get(
                "adaptive_performance", 0.0
            )
            integration_stability = current_system_metrics.get(
                "integration_stability", 0.0
            )

            # Phase B総合効果計算
            current_phase_b_effect = (
                phase_b_efficiency + settings_manager_performance * 0.1
            )

            # ベースライン比較
            phase_b_baseline = (
                baseline_measurement.get_baseline("phase_b_efficiency") or 66.8
            )

            # 保護状況評価
            improvement, improvement_percentage = (
                self.statistical_analyzer.calculate_improvement(
                    phase_b_baseline, current_phase_b_effect
                )
            )

            # 保護成功判定
            preservation_success = (
                current_phase_b_effect
                >= self.success_criteria["phase_b_preservation_threshold"]
            )

            # 信頼度計算
            stability_factor = min(1.0, integration_stability)
            confidence_level = 0.9 if preservation_success else 0.3
            confidence_level *= stability_factor

            # 統計的有意性
            statistical_significance = (
                preservation_success and abs(improvement) < 1.0
            )  # 大幅変動なし

            # 測定結果構築
            phase_b_measurement = MeasurementResult(
                measurement_type="phase_b_preservation",
                baseline_value=phase_b_baseline,
                current_value=current_phase_b_effect,
                improvement=improvement,
                improvement_percentage=improvement_percentage,
                measurement_time=time.time() - measurement_start,
                confidence_level=confidence_level,
                statistical_significance=statistical_significance,
                metadata={
                    "preservation_success": preservation_success,
                    "efficiency_threshold": self.success_criteria[
                        "phase_b_preservation_threshold"
                    ],
                    "adaptive_performance": settings_manager_performance,
                    "integration_stability": integration_stability,
                    "measurement_timestamp": time.time(),
                },
            )

            # 継続測定データ更新
            self._update_continuous_measurement(
                "phase_b_efficiency", current_phase_b_effect
            )

            self.logger.info(
                f"Phase B preservation validated: {current_phase_b_effect:.1f}% "
                f"(threshold: {self.success_criteria['phase_b_preservation_threshold']}%)"
            )
            return phase_b_measurement

        except Exception as e:
            self.logger.error(f"Phase B preservation validation failed: {e}")
            return MeasurementResult(
                measurement_type="phase_b_preservation",
                baseline_value=66.8,
                current_value=0.0,
                improvement=0.0,
                improvement_percentage=0.0,
                measurement_time=0.0,
                confidence_level=0.0,
                statistical_significance=False,
                metadata={"error": str(e)},
            )

    def measure_performance(self, data: Any) -> Dict[str, Any]:
        """パフォーマンス測定実行"""
        try:
            start_time = time.time()

            # 基本パフォーマンス指標
            processing_time = time.time() - start_time
            throughput = len(str(data)) / processing_time if processing_time > 0 else 0

            # メモリ使用量（簡易測定）
            import sys

            memory_usage = sys.getsizeof(data)

            return {
                "processing_time": processing_time,
                "throughput": throughput,
                "memory_usage": memory_usage,
                "efficiency_score": (
                    throughput / memory_usage if memory_usage > 0 else 0
                ),
                "measurement_timestamp": time.time(),
            }
        except Exception as e:
            self.logger.error(f"Performance measurement failed: {e}")
            return {"error": str(e)}

    def calculate_efficiency(self, results: Any) -> Dict[str, Any]:
        """効率計算"""
        try:
            if not isinstance(results, dict):
                return {"error": "Invalid results format"}

            processing_time = results.get("processing_time", 0)
            memory_usage = results.get("memory_usage", 0)
            throughput = results.get("throughput", 0)

            # 効率指標計算
            time_efficiency = 1.0 / processing_time if processing_time > 0 else 0
            memory_efficiency = throughput / memory_usage if memory_usage > 0 else 0
            overall_efficiency = (time_efficiency + memory_efficiency) / 2

            return {
                "time_efficiency": time_efficiency,
                "memory_efficiency": memory_efficiency,
                "overall_efficiency": overall_efficiency,
                "efficiency_rating": (
                    "high"
                    if overall_efficiency > 0.8
                    else "medium" if overall_efficiency > 0.5 else "low"
                ),
            }
        except Exception as e:
            self.logger.error(f"Efficiency calculation failed: {e}")
            return {"error": str(e)}

    def analyze_trend(self, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """パフォーマンストレンド分析"""
        try:
            if metric_name not in self.continuous_measurements:
                return {"error": f"Metric {metric_name} not found"}

            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 3600)  # days前まで

            # 期間内データ抽出
            relevant_data = [
                (timestamp, value)
                for timestamp, value in self.continuous_measurements[metric_name]
                if timestamp >= cutoff_time
            ]

            if len(relevant_data) < 2:
                return {"error": "Insufficient data for trend analysis"}

            # トレンド検出
            trend = self.statistical_analyzer.detect_trend(relevant_data)

            # 統計計算
            values = [value for _, value in relevant_data]
            mean_value = sum(values) / len(values)
            min_value = min(values)
            max_value = max(values)

            return {
                "metric_name": metric_name,
                "trend": trend,
                "data_points": len(relevant_data),
                "mean_value": mean_value,
                "min_value": min_value,
                "max_value": max_value,
                "analysis_period_days": days,
                "analysis_timestamp": current_time,
            }
        except Exception as e:
            self.logger.error(f"Trend analysis failed for {metric_name}: {e}")
            return {"error": str(e)}

    def _update_continuous_measurement(self, metric_name: str, value: float) -> None:
        """継続測定データ更新"""
        try:
            current_time = time.time()
            if metric_name not in self.continuous_measurements:
                self.continuous_measurements[metric_name] = []

            self.continuous_measurements[metric_name].append((current_time, value))

            # 古いデータのクリーンアップ（30日以前）
            cutoff_time = current_time - (30 * 24 * 3600)
            self.continuous_measurements[metric_name] = [
                (timestamp, val)
                for timestamp, val in self.continuous_measurements[metric_name]
                if timestamp >= cutoff_time
            ]
        except Exception as e:
            self.logger.error(f"Continuous measurement update failed: {e}")
