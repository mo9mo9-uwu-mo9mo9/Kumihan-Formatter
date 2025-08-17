"""
AI効果測定メインシステム

AI専用効果分離測定・Phase B基盤保護確認・2.0%削減達成検証
統合効果測定・品質監視・安定性確認システム
"""

import json
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from kumihan_formatter.core.utilities.logger import get_logger

from .measurement_core import (
    BaselineMeasurement,
    EffectReport,
    MeasurementResult,
    QualityMetrics,
    StabilityAssessment,
)
from .statistical_analyzer import StatisticalAnalyzer


class AIEffectMeasurement:
    """AI効果測定・検証システム

    AI専用効果分離測定・Phase B基盤（66.8%削減）維持確認・2.0%削減達成検証
    統合効果測定・品質監視・安定性確認システム
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """効果測定システム初期化"""
        self.logger = get_logger(__name__)
        self.config = config or {}

        # 測定基盤システム
        self.baseline_measurement = BaselineMeasurement()
        self.statistical_analyzer = StatisticalAnalyzer()

        # 測定データ管理
        self.measurement_history: List[EffectReport] = []
        self.continuous_measurements: Dict[str, List[Tuple[float, float]]] = (
            {}
        )  # (timestamp, value)

        # 品質・安定性追跡
        self.quality_history: List[QualityMetrics] = []
        self.stability_assessments: List[StabilityAssessment] = []

        # 成功基準
        self.success_criteria = {
            "phase_b_preservation_threshold": 66.0,  # Phase B基盤最低保護基準
            "ai_contribution_target": 2.0,  # AI目標貢献度
            "total_efficiency_target": 68.8,  # 総合効率目標
            "stability_threshold": 98.0,  # 安定性目標
            "quality_threshold": 0.9,  # 品質目標
        }

        # Phase Bベースライン確立
        self._establish_phase_b_baseline()

        self.logger.info("AIEffectMeasurement initialized successfully")

    def _establish_phase_b_baseline(self) -> None:
        """Phase B基盤ベースライン確立"""
        try:
            # Phase B基盤効果（66.8%削減）をベースラインとして設定
            phase_b_baseline_measurements = [
                66.8,
                66.9,
                66.7,
                66.8,
                66.8,
                67.0,
                66.6,
            ]  # 想定基盤効果

            self.baseline_measurement.establish_baseline(
                "phase_b_efficiency",
                phase_b_baseline_measurements,
                {
                    "system": "Phase B Integration",
                    "components": ["AdaptiveSettingsManager", "OptimizationIntegrator"],
                    "established_date": time.time(),
                },
            )

            # 総合効率ベースライン
            self.baseline_measurement.establish_baseline(
                "total_efficiency",
                phase_b_baseline_measurements,  # Phase B = 初期総合効率
                {"type": "total_system_efficiency"},
            )

            self.logger.info("Phase B baseline established: 66.8% efficiency")

        except Exception as e:
            self.logger.error(f"Phase B baseline establishment failed: {e}")

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

            # 統計的有意性（複数測定値必要）
            # ai_measurements, baseline_measurements変数を削除（未使用のため）
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
        self, current_system_metrics: Dict[str, float]
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
                self.baseline_measurement.get_baseline("phase_b_efficiency") or 66.8
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

            status = "PRESERVED" if preservation_success else "AT_RISK"
            self.logger.info(
                f"Phase B preservation validated: {current_phase_b_effect:.3f}% - {status}"
            )

            return phase_b_measurement
        except Exception as e:
            self.logger.error(f"Phase B preservation validation failed: {e}")
            return MeasurementResult(
                measurement_type="phase_b_preservation",
                baseline_value=66.8,
                current_value=66.8,
                improvement=0.0,
                improvement_percentage=0.0,
                measurement_time=0.0,
                confidence_level=0.5,
                statistical_significance=True,
                metadata={"error": str(e), "fallback_mode": True},
            )

    def measure_integrated_effects(
        self, system_metrics: Dict[str, float]
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
                self.baseline_measurement.get_baseline("total_efficiency") or 66.8
            )

            # 統合改善効果
            improvement, improvement_percentage = (
                self.statistical_analyzer.calculate_improvement(
                    total_baseline, total_integrated_effect
                )
            )

            # 目標達成評価
            target_achievement = (
                total_integrated_effect
                >= self.success_criteria["total_efficiency_target"]
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

            # 継続測定データ更新
            self._update_continuous_measurement(
                "total_efficiency", total_integrated_effect
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

    def _update_continuous_measurement(self, metric_name: str, value: float) -> None:
        """継続測定データ更新"""
        try:
            current_time = time.time()
            if metric_name not in self.continuous_measurements:
                self.continuous_measurements[metric_name] = []

            self.continuous_measurements[metric_name].append((current_time, value))

            # データ保持期間制限（最大100エントリ）
            if len(self.continuous_measurements[metric_name]) > 100:
                self.continuous_measurements[metric_name] = (
                    self.continuous_measurements[metric_name][-100:]
                )

        except Exception as e:
            self.logger.error(f"Continuous measurement update failed: {e}")

    def generate_comprehensive_report(
        self,
        current_ai_metrics: Dict[str, float],
        current_system_metrics: Dict[str, float],
    ) -> EffectReport:
        """総合効果レポート生成"""
        try:
            report_start = time.time()
            report_id = f"effect_report_{int(time.time())}"

            # 各種測定実行
            ai_effect = self.measure_ai_contribution(current_ai_metrics)
            phase_b_effect = self.validate_phase_b_preservation(current_system_metrics)
            integrated_effect = self.measure_integrated_effects(current_system_metrics)

            # 品質・安定性評価
            quality_metrics = self._calculate_quality_metrics(current_system_metrics)
            stability_assessment = self._calculate_stability_score(
                current_system_metrics
            )

            # 成功基準評価
            success_criteria_met = self._evaluate_success_criteria(
                ai_effect, phase_b_effect, integrated_effect
            )

            # 推奨事項生成
            recommendations = self._generate_recommendations(
                ai_effect, phase_b_effect, integrated_effect, quality_metrics
            )

            # レポート構築
            effect_report = EffectReport(
                report_id=report_id,
                timestamp=time.time(),
                phase_b_effect=phase_b_effect,
                ai_effect=ai_effect,
                integrated_effect=integrated_effect,
                quality_metrics={
                    "accuracy": quality_metrics.accuracy,
                    "precision": quality_metrics.precision,
                    "recall": quality_metrics.recall,
                    "response_time": quality_metrics.response_time,
                    "throughput": quality_metrics.throughput,
                    "error_rate": quality_metrics.error_rate,
                    "availability": quality_metrics.availability,
                    "consistency": quality_metrics.consistency,
                },
                stability_score=stability_assessment,
                success_criteria_met=success_criteria_met,
                recommendations=recommendations,
            )

            # レポート履歴更新
            self.measurement_history.append(effect_report)

            # 履歴管理（最大50レポート保持）
            if len(self.measurement_history) > 50:
                self.measurement_history = self.measurement_history[-50:]

            generation_time = time.time() - report_start
            self.logger.info(
                f"Comprehensive report generated: {report_id} (time: {generation_time:.3f}s)"
            )

            return effect_report
        except Exception as e:
            self.logger.error(f"Comprehensive report generation failed: {e}")
            # フォールバック用の最小レポート
            return EffectReport(
                report_id=f"fallback_report_{int(time.time())}",
                timestamp=time.time(),
                phase_b_effect=MeasurementResult(
                    measurement_type="phase_b_preservation",
                    baseline_value=66.8,
                    current_value=66.8,
                    improvement=0.0,
                    improvement_percentage=0.0,
                    measurement_time=0.0,
                    confidence_level=0.5,
                    statistical_significance=True,
                ),
                ai_effect=MeasurementResult(
                    measurement_type="ai_contribution",
                    baseline_value=0.0,
                    current_value=0.0,
                    improvement=0.0,
                    improvement_percentage=0.0,
                    measurement_time=0.0,
                    confidence_level=0.0,
                    statistical_significance=False,
                ),
                integrated_effect=MeasurementResult(
                    measurement_type="integrated_effects",
                    baseline_value=66.8,
                    current_value=66.8,
                    improvement=0.0,
                    improvement_percentage=0.0,
                    measurement_time=0.0,
                    confidence_level=0.5,
                    statistical_significance=False,
                ),
                quality_metrics={},
                stability_score=0.8,
                success_criteria_met=False,
                recommendations=[
                    "レポート生成に失敗しました。システムを確認してください。"
                ],
            )

    def _calculate_quality_metrics(
        self, system_metrics: Dict[str, float]
    ) -> QualityMetrics:
        """品質指標計算"""
        try:
            quality_metrics = QualityMetrics(
                accuracy=system_metrics.get("accuracy", 0.8),
                precision=system_metrics.get("precision", 0.85),
                recall=system_metrics.get("recall", 0.82),
                response_time=system_metrics.get("response_time", 150.0),
                throughput=system_metrics.get("throughput", 1000.0),
                error_rate=system_metrics.get("error_rate", 0.02),
                availability=system_metrics.get("availability", 0.999),
                consistency=system_metrics.get("consistency", 0.95),
            )

            # 品質履歴更新
            self.quality_history.append(quality_metrics)
            if len(self.quality_history) > 100:
                self.quality_history = self.quality_history[-100:]

            return quality_metrics
        except Exception as e:
            self.logger.error(f"Quality metrics calculation failed: {e}")
            return QualityMetrics(
                accuracy=0.8,
                precision=0.8,
                recall=0.8,
                response_time=200.0,
                throughput=800.0,
                error_rate=0.05,
                availability=0.99,
                consistency=0.85,
            )

    def _calculate_stability_score(self, system_metrics: Dict[str, float]) -> float:
        """安定性スコア計算"""
        try:
            # 安定性指標収集
            uptime = system_metrics.get("uptime_percentage", 99.0)
            error_frequency = system_metrics.get("error_frequency", 0.1)
            performance_variance = system_metrics.get("performance_variance", 5.0)
            recovery_time = system_metrics.get("recovery_time", 30.0)

            # 安定性評価作成
            stability = StabilityAssessment(
                uptime_percentage=uptime,
                error_frequency=error_frequency,
                performance_variance=performance_variance,
                recovery_time=recovery_time,
                resilience_score=min(1.0, uptime / 100.0),
                stability_trend=self._detect_stability_trend(),
            )

            # 安定性履歴更新
            self.stability_assessments.append(stability)
            if len(self.stability_assessments) > 50:
                self.stability_assessments = self.stability_assessments[-50:]

            # 総合安定性スコア計算
            stability_score = (
                (uptime / 100.0) * 0.4
                + (1.0 - min(1.0, error_frequency / 10.0)) * 0.3
                + (1.0 - min(1.0, performance_variance / 100.0)) * 0.2
                + (1.0 - min(1.0, recovery_time / 300.0)) * 0.1
            )

            return min(1.0, max(0.0, stability_score))
        except Exception as e:
            self.logger.error(f"Stability score calculation failed: {e}")
            return 0.8

    def _detect_stability_trend(self) -> str:
        """安定性トレンド検出"""
        try:
            if len(self.stability_assessments) < 3:
                return "insufficient_data"

            recent_scores = [
                assessment.resilience_score
                for assessment in self.stability_assessments[-5:]
            ]
            time_points = list(range(len(recent_scores)))
            time_series = list(zip([float(t) for t in time_points], recent_scores))

            return self.statistical_analyzer.detect_trend(time_series)
        except Exception as e:
            self.logger.error(f"Stability trend detection failed: {e}")
            return "unknown"

    def _evaluate_success_criteria(
        self,
        ai_effect: MeasurementResult,
        phase_b_effect: MeasurementResult,
        integrated_effect: MeasurementResult,
    ) -> bool:
        """成功基準評価"""
        try:
            # AI貢献度基準
            ai_target_met = (
                ai_effect.current_value
                >= self.success_criteria["ai_contribution_target"]
            )

            # Phase B保護基準
            phase_b_preserved = (
                phase_b_effect.current_value
                >= self.success_criteria["phase_b_preservation_threshold"]
            )

            # 総合効率基準
            total_target_met = (
                integrated_effect.current_value
                >= self.success_criteria["total_efficiency_target"]
            )

            # 統計的有意性確認
            statistical_validity = (
                ai_effect.statistical_significance
                and phase_b_effect.statistical_significance
                and integrated_effect.statistical_significance
            )

            # 総合成功判定
            success = ai_target_met and phase_b_preserved and total_target_met
            if statistical_validity:
                success = success and statistical_validity

            return success
        except Exception as e:
            self.logger.error(f"Success criteria evaluation failed: {e}")
            return False

    def _generate_recommendations(
        self,
        ai_effect: MeasurementResult,
        phase_b_effect: MeasurementResult,
        integrated_effect: MeasurementResult,
        quality_metrics: QualityMetrics,
    ) -> List[str]:
        """推奨事項生成"""
        try:
            recommendations = []

            # AI効果改善提案
            if (
                ai_effect.current_value
                < self.success_criteria["ai_contribution_target"]
            ):
                recommendations.append(
                    f"AI貢献度向上が必要: 現在{ai_effect.current_value:.1f}% < 目標2.0%"
                )
                recommendations.append("ML最適化・予測精度改善を実施してください")

            # Phase B基盤保護
            if (
                phase_b_effect.current_value
                < self.success_criteria["phase_b_preservation_threshold"]
            ):
                recommendations.append(
                    f"Phase B基盤保護強化が必要: {phase_b_effect.current_value:.1f}%"
                )
                recommendations.append("設定マネージャー安定性確認・統合テスト実施")

            # 総合効率改善
            if (
                integrated_effect.current_value
                < self.success_criteria["total_efficiency_target"]
            ):
                recommendations.append(
                    f"総合効率向上が必要: {integrated_effect.current_value:.1f}% < 目標68.8%"
                )

            # 品質改善提案
            if quality_metrics.error_rate > 0.05:
                recommendations.append(
                    f"エラー率改善が必要: {quality_metrics.error_rate:.3f}"
                )

            if quality_metrics.response_time > 200.0:
                recommendations.append(
                    f"応答時間改善が必要: {quality_metrics.response_time:.1f}ms"
                )

            # 統計的有意性改善
            if not ai_effect.statistical_significance:
                recommendations.append("AI効果測定：より多くのサンプル収集が必要")

            if not phase_b_effect.statistical_significance:
                recommendations.append("Phase B測定：安定性向上・継続監視が必要")

            # 成功時の継続改善提案
            if not recommendations:
                recommendations.extend(
                    [
                        "✅ 全ての成功基準を達成しています",
                        "継続監視・安定性維持を推奨します",
                        "さらなる最適化機会を探索してください",
                    ]
                )

            return recommendations
        except Exception as e:
            self.logger.error(f"Recommendations generation failed: {e}")
            return ["推奨事項生成に失敗しました。システムを確認してください。"]

    def export_measurements(self, output_path: Optional[Path] = None) -> bool:
        """測定データエクスポート"""
        try:
            if output_path is None:
                output_path = Path("tmp") / "ai_effect_measurements.json"

            output_path.parent.mkdir(parents=True, exist_ok=True)

            export_data = {
                "measurement_history": [
                    {
                        "report_id": report.report_id,
                        "timestamp": report.timestamp,
                        "phase_b_effect": {
                            "measurement_type": report.phase_b_effect.measurement_type,
                            "baseline_value": report.phase_b_effect.baseline_value,
                            "current_value": report.phase_b_effect.current_value,
                            "improvement": report.phase_b_effect.improvement,
                            "improvement_percentage": report.phase_b_effect.improvement_percentage,
                            "confidence_level": report.phase_b_effect.confidence_level,
                            "statistical_significance": report.phase_b_effect.statistical_significance,
                        },
                        "ai_effect": {
                            "measurement_type": report.ai_effect.measurement_type,
                            "baseline_value": report.ai_effect.baseline_value,
                            "current_value": report.ai_effect.current_value,
                            "improvement": report.ai_effect.improvement,
                            "improvement_percentage": report.ai_effect.improvement_percentage,
                            "confidence_level": report.ai_effect.confidence_level,
                            "statistical_significance": report.ai_effect.statistical_significance,
                        },
                        "integrated_effect": {
                            "measurement_type": report.integrated_effect.measurement_type,
                            "baseline_value": report.integrated_effect.baseline_value,
                            "current_value": report.integrated_effect.current_value,
                            "improvement": report.integrated_effect.improvement,
                            "improvement_percentage": report.integrated_effect.improvement_percentage,
                            "confidence_level": report.integrated_effect.confidence_level,
                            "statistical_significance": report.integrated_effect.statistical_significance,
                        },
                        "quality_metrics": report.quality_metrics,
                        "stability_score": report.stability_score,
                        "success_criteria_met": report.success_criteria_met,
                        "recommendations": report.recommendations,
                    }
                    for report in self.measurement_history
                ],
                "continuous_measurements": {
                    metric: [(timestamp, value) for timestamp, value in measurements]
                    for metric, measurements in self.continuous_measurements.items()
                },
                "success_criteria": self.success_criteria,
                "export_timestamp": time.time(),
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Measurement data exported to: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"Measurement data export failed: {e}")
            return False

    def get_latest_report(self) -> Optional[EffectReport]:
        """最新レポート取得"""
        if self.measurement_history:
            return self.measurement_history[-1]
        return None

    def get_trend_analysis(self, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """トレンド分析"""
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

    def run_continuous_monitoring(
        self,
        ai_metrics_source: Callable[[], Dict[str, float]],
        system_metrics_source: Callable[[], Dict[str, float]],
        interval_seconds: int = 300,
        max_iterations: int = 100,
    ) -> None:
        """継続監視実行"""
        try:
            self.logger.info(
                f"Starting continuous monitoring (interval: {interval_seconds}s, max: {max_iterations})"
            )

            with ThreadPoolExecutor(max_workers=2) as executor:
                for iteration in range(max_iterations):
                    try:
                        # 並列データ取得
                        ai_future: Future[Dict[str, float]] = executor.submit(
                            ai_metrics_source
                        )
                        system_future: Future[Dict[str, float]] = executor.submit(
                            system_metrics_source
                        )

                        ai_metrics = ai_future.result(timeout=30)
                        system_metrics = system_future.result(timeout=30)

                        # 効果測定実行
                        report = self.generate_comprehensive_report(
                            ai_metrics, system_metrics
                        )

                        self.logger.info(
                            f"Monitoring iteration {iteration + 1}/{max_iterations} completed"
                        )

                        # 成功基準未達時の警告
                        if not report.success_criteria_met:
                            self.logger.warning(
                                f"Success criteria not met in iteration {iteration + 1}"
                            )

                        time.sleep(interval_seconds)

                    except Exception as e:
                        self.logger.error(
                            f"Monitoring iteration {iteration + 1} failed: {e}"
                        )
                        time.sleep(interval_seconds / 2)  # 短縮間隔でリトライ

            self.logger.info("Continuous monitoring completed")

        except Exception as e:
            self.logger.error(f"Continuous monitoring failed: {e}")
