"""
ビジネス指標・ROI計算モジュール

ROI計算・コスト分析・ビジネス価値測定・投資対効果評価
レポート生成支援・成功基準評価・推奨事項生成
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger

from ..measurement_core import EffectReport, MeasurementResult, QualityMetrics


class BusinessMetrics:
    """ビジネス指標・ROI計算専用クラス

    ROI計算・コスト分析・ビジネス価値測定
    投資対効果評価・レポート生成支援・成功基準評価
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """ビジネス測定システム初期化"""
        self.logger = get_logger(__name__)
        self.config = config or {}

        # ビジネス成功基準
        self.success_criteria = self.config.get(
            "success_criteria",
            {
                "ai_contribution_target": 2.0,  # AI貢献度目標2.0%
                "phase_b_preservation_threshold": 66.0,  # Phase B保護基準66%
                "total_efficiency_target": 68.8,  # 総合効率目標68.8%
                "measurement_confidence_threshold": 0.8,  # 測定信頼度基準80%
                "roi_target": 1.5,  # ROI目標150%
                "cost_reduction_target": 0.20,  # コスト削減目標20%
            },
        )

        # レポート履歴
        self.measurement_history: List[EffectReport] = []

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

    def calculate_roi(
        self, investment_cost: float, benefit_value: float
    ) -> Dict[str, Any]:
        """ROI計算"""
        try:
            if investment_cost <= 0:
                return {"error": "Invalid investment cost"}

            roi = (benefit_value - investment_cost) / investment_cost
            roi_percentage = roi * 100

            # ROI評価
            if roi >= self.success_criteria["roi_target"]:
                roi_assessment = "excellent"
            elif roi >= 1.0:
                roi_assessment = "good"
            elif roi >= 0.5:
                roi_assessment = "acceptable"
            else:
                roi_assessment = "poor"

            return {
                "roi": roi,
                "roi_percentage": roi_percentage,
                "investment_cost": investment_cost,
                "benefit_value": benefit_value,
                "net_benefit": benefit_value - investment_cost,
                "roi_assessment": roi_assessment,
                "target_met": roi >= self.success_criteria["roi_target"],
                "calculation_timestamp": time.time(),
            }
        except Exception as e:
            self.logger.error(f"ROI calculation failed: {e}")
            return {"error": str(e)}

    def calculate_cost_reduction(
        self, original_cost: float, optimized_cost: float
    ) -> Dict[str, Any]:
        """コスト削減計算"""
        try:
            if original_cost <= 0:
                return {"error": "Invalid original cost"}

            cost_reduction = original_cost - optimized_cost
            reduction_percentage = cost_reduction / original_cost

            # コスト削減評価
            if reduction_percentage >= self.success_criteria["cost_reduction_target"]:
                reduction_assessment = "target_achieved"
            elif reduction_percentage >= 0.1:
                reduction_assessment = "good_progress"
            elif reduction_percentage > 0:
                reduction_assessment = "minimal_progress"
            else:
                reduction_assessment = "no_improvement"

            return {
                "original_cost": original_cost,
                "optimized_cost": optimized_cost,
                "cost_reduction": cost_reduction,
                "reduction_percentage": reduction_percentage,
                "reduction_assessment": reduction_assessment,
                "target_met": reduction_percentage
                >= self.success_criteria["cost_reduction_target"],
                "calculation_timestamp": time.time(),
            }
        except Exception as e:
            self.logger.error(f"Cost reduction calculation failed: {e}")
            return {"error": str(e)}

    def measure_business_value(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """ビジネス価値測定"""
        try:
            # ビジネス価値指標
            productivity_gain = metrics.get("productivity_gain", 0.0)
            time_savings = metrics.get("time_savings", 0.0)
            quality_improvement = metrics.get("quality_improvement", 0.0)
            customer_satisfaction = metrics.get("customer_satisfaction", 0.0)

            # ビジネス価値スコア計算
            business_value_score = (
                productivity_gain * 0.3
                + time_savings * 0.25
                + quality_improvement * 0.25
                + customer_satisfaction * 0.2
            )

            # 価値評価
            if business_value_score >= 0.8:
                value_assessment = "high_value"
            elif business_value_score >= 0.6:
                value_assessment = "medium_value"
            elif business_value_score >= 0.4:
                value_assessment = "low_value"
            else:
                value_assessment = "minimal_value"

            return {
                "productivity_gain": productivity_gain,
                "time_savings": time_savings,
                "quality_improvement": quality_improvement,
                "customer_satisfaction": customer_satisfaction,
                "business_value_score": business_value_score,
                "value_assessment": value_assessment,
                "measurement_timestamp": time.time(),
            }
        except Exception as e:
            self.logger.error(f"Business value measurement failed: {e}")
            return {"error": str(e)}

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
                            "statistical_significance": (
                                report.phase_b_effect.statistical_significance
                            ),
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
                            "current_value": (report.integrated_effect.current_value),
                            "improvement": report.integrated_effect.improvement,
                            "improvement_percentage": (
                                report.integrated_effect.improvement_percentage
                            ),
                            "confidence_level": report.integrated_effect.confidence_level,
                            "statistical_significance": (
                                report.integrated_effect.statistical_significance
                            ),
                        },
                        "quality_metrics": report.quality_metrics,
                        "stability_score": report.stability_score,
                        "success_criteria_met": report.success_criteria_met,
                        "recommendations": report.recommendations,
                    }
                    for report in self.measurement_history
                ],
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

    def generate_business_report(self, measurements: Dict[str, Any]) -> Dict[str, Any]:
        """ビジネスレポート生成"""
        try:
            # ビジネス指標計算
            roi_data = self.calculate_roi(
                measurements.get("investment_cost", 100000),
                measurements.get("benefit_value", 150000),
            )

            cost_reduction_data = self.calculate_cost_reduction(
                measurements.get("original_cost", 200000),
                measurements.get("optimized_cost", 160000),
            )

            business_value_data = self.measure_business_value(measurements)

            # 総合評価
            overall_success = (
                roi_data.get("target_met", False)
                and cost_reduction_data.get("target_met", False)
                and business_value_data.get("business_value_score", 0) >= 0.6
            )

            return {
                "roi_analysis": roi_data,
                "cost_reduction_analysis": cost_reduction_data,
                "business_value_analysis": business_value_data,
                "overall_success": overall_success,
                "report_timestamp": time.time(),
            }
        except Exception as e:
            self.logger.error(f"Business report generation failed: {e}")
            return {"error": str(e)}
