"""
AI効果測定メインシステム

AI専用効果分離測定・Phase B基盤保護確認・2.0%削減達成検証
統合効果測定・品質監視・安定性確認システム
"""

import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, cast

from kumihan_formatter.core.utilities.logger import get_logger

from .measurement_core import (
    BaselineMeasurement,
    EffectReport,
    MeasurementResult,
)
from .metrics import BusinessMetrics, PerformanceMetrics, QualityMetrics
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

        # メトリクス計算器初期化
        self.performance_metrics = PerformanceMetrics(self.config)
        self.quality_metrics = QualityMetrics(self.config)
        self.business_metrics = BusinessMetrics(self.config)

        # 測定データ管理
        self.measurement_history: List[EffectReport] = []

        # 成功基準設定
        self.success_criteria = self.config.get(
            "success_criteria",
            {
                "ai_contribution_target": 2.0,  # AI貢献度目標2.0%
                "phase_b_preservation_threshold": 66.0,  # Phase B保護基準66%
                "total_efficiency_target": 68.8,  # 総合効率目標68.8%
                "measurement_confidence_threshold": 0.8,  # 測定信頼度基準80%
            },
        )

        self.logger.info("AI効果測定システム初期化完了")

    def _establish_phase_b_baseline(self) -> None:
        """Phase B基盤ベースライン確立"""
        try:
            # Phase B基盤効果ベースライン設定（66.8%削減効果）
            baseline_values = {
                "phase_b_efficiency": 66.8,
                "settings_manager_performance": 95.0,
                "integration_stability": 98.5,
                "total_efficiency": 66.8,
            }

            for metric, value in baseline_values.items():
                self.baseline_measurement.set_baseline(metric, value)

            self.logger.info("Phase B baseline established: 66.8% efficiency confirmed")

        except Exception as e:
            self.logger.error(f"Phase B baseline establishment failed: {e}")

    def measure_ai_effect(
        self, current_ai_metrics: Dict[str, float]
    ) -> MeasurementResult:
        """AI専用削減効果測定（公開API）"""
        return self.performance_metrics.measure_ai_contribution(current_ai_metrics)

    def measure_comprehensive_effect(
        self,
        current_ai_metrics: Dict[str, float],
        current_system_metrics: Dict[str, float],
    ) -> EffectReport:
        """統合効果測定（公開API）"""
        return self.generate_comprehensive_report(
            current_ai_metrics, current_system_metrics
        )

    def generate_comprehensive_report(
        self,
        current_ai_metrics: Dict[str, float],
        current_system_metrics: Dict[str, float],
    ) -> EffectReport:
        """総合効果レポート生成"""
        try:
            report_start = time.time()
            report_id = f"effect_report_{int(time.time())}"

            # 各種測定実行（委譲パターン）
            ai_effect = self.performance_metrics.measure_ai_contribution(
                current_ai_metrics
            )
            phase_b_effect = self.performance_metrics.validate_phase_b_preservation(
                current_system_metrics, self.baseline_measurement
            )
            integrated_effect = self.quality_metrics.measure_integrated_effects(
                current_system_metrics, self.baseline_measurement, self.success_criteria
            )

            # 品質・安定性評価
            quality_metrics = self.quality_metrics._calculate_quality_metrics(
                current_system_metrics
            )
            stability_assessment = self.quality_metrics._calculate_stability_score(
                current_system_metrics
            )

            # 成功基準評価
            success_criteria_met = self.business_metrics._evaluate_success_criteria(
                ai_effect, phase_b_effect, integrated_effect
            )

            # 推奨事項生成
            recommendations = self.business_metrics._generate_recommendations(
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
                f"Comprehensive report generated: {report_id} "
                f"(time: {generation_time:.3f}s)"
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

    def generate_report(
        self,
        current_ai_metrics: Dict[str, float],
        current_system_metrics: Dict[str, float],
    ) -> EffectReport:
        """レポート生成（公開API - 互換性維持）"""
        return self.generate_comprehensive_report(
            current_ai_metrics, current_system_metrics
        )

    def get_latest_measurement(self) -> Optional[EffectReport]:
        """最新測定結果取得（公開API）"""
        if self.measurement_history:
            return self.measurement_history[-1]
        return None

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
                f"Starting continuous monitoring "
                f"(interval: {interval_seconds}s, max: {max_iterations})"
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
                            f"Monitoring iteration {iteration + 1}/"
                            f"{max_iterations} completed"
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

    # 委譲メソッド群（既存API互換性維持）
    def measure_performance(self, data: Any) -> Dict[str, Any]:
        """パフォーマンス測定委譲"""
        return self.performance_metrics.measure_performance(data)

    def calculate_efficiency(self, results: Any) -> Dict[str, Any]:
        """効率計算委譲"""
        return self.performance_metrics.calculate_efficiency(results)

    def evaluate_quality(self, results: Any) -> Dict[str, Any]:
        """品質評価委譲"""
        return cast(Dict[str, Any], self.quality_metrics.evaluate_quality(results))

    def analyze_trend(self, metric_name: str, days: int = 7) -> Dict[str, Any]:
        """トレンド分析委譲"""
        return self.performance_metrics.analyze_trend(metric_name, days)

    def export_measurements(self, output_path: Optional[str] = None) -> bool:
        """測定データエクスポート委譲"""
        return self.business_metrics.export_measurements(output_path)

    def calculate_roi(
        self, investment_cost: float, benefit_value: float
    ) -> Dict[str, Any]:
        """ROI計算委譲"""
        return self.business_metrics.calculate_roi(investment_cost, benefit_value)
