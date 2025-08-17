"""
測定データ構造・コア機能

AI効果測定システムの基本データ構造とベースライン管理
"""

import statistics
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from kumihan_formatter.core.utilities.logger import get_logger


@dataclass
class MeasurementResult:
    """測定結果"""

    measurement_type: str
    baseline_value: float
    current_value: float
    improvement: float
    improvement_percentage: float
    measurement_time: float
    confidence_level: float
    statistical_significance: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EffectReport:
    """効果レポート"""

    report_id: str
    timestamp: float
    phase_b_effect: MeasurementResult
    ai_effect: MeasurementResult
    integrated_effect: MeasurementResult
    quality_metrics: Dict[str, float]
    stability_score: float
    success_criteria_met: bool
    recommendations: List[str]


@dataclass
class QualityMetrics:
    """品質指標"""

    accuracy: float
    precision: float
    recall: float
    response_time: float
    throughput: float
    error_rate: float
    availability: float
    consistency: float


@dataclass
class StabilityAssessment:
    """安定性評価"""

    uptime_percentage: float
    error_frequency: float
    performance_variance: float
    recovery_time: float
    resilience_score: float
    stability_trend: str


class BaselineMeasurement:
    """ベースライン測定管理"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__ + ".BaselineMeasurement")
        self.baselines: Dict[str, float] = {}
        self.baseline_history: List[Dict[str, Any]] = []
        self.measurement_metadata: Dict[str, Dict[str, Any]] = {}

    def establish_baseline(
        self,
        metric_name: str,
        measurements: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> float:
        """ベースライン確立"""
        try:
            if not measurements:
                raise ValueError("No measurements provided for baseline")

            # 統計的ベースライン計算
            baseline_value = statistics.median(
                measurements
            )  # 中央値使用（異常値に頑健）

            # ベースライン記録
            self.baselines[metric_name] = baseline_value
            self.measurement_metadata[metric_name] = {
                "sample_count": len(measurements),
                "mean": statistics.mean(measurements),
                "median": baseline_value,
                "std_dev": (
                    statistics.stdev(measurements) if len(measurements) > 1 else 0.0
                ),
                "min_value": min(measurements),
                "max_value": max(measurements),
                "established_at": time.time(),
                "metadata": metadata or {},
            }

            # 履歴記録
            self.baseline_history.append(
                {
                    "metric_name": metric_name,
                    "baseline_value": baseline_value,
                    "timestamp": time.time(),
                    "measurement_count": len(measurements),
                }
            )

            self.logger.info(
                f"Baseline established for {metric_name}: {baseline_value:.3f}"
            )
            return baseline_value
        except Exception as e:
            self.logger.error(f"Baseline establishment failed for {metric_name}: {e}")
            return 0.0

    def get_baseline(self, metric_name: str) -> Optional[float]:
        """ベースライン取得"""
        return self.baselines.get(metric_name)

    def get_baseline_metadata(self, metric_name: str) -> Dict[str, Any]:
        """ベースラインメタデータ取得"""
        return self.measurement_metadata.get(metric_name, {})

    def update_baseline(self, metric_name: str, new_measurements: List[float]) -> bool:
        """ベースライン更新"""
        try:
            if not new_measurements:
                return False

            # 新しいベースライン確立
            old_baseline = self.baselines.get(metric_name, 0.0)
            new_baseline = self.establish_baseline(metric_name, new_measurements)

            self.logger.info(
                f"Baseline updated for {metric_name}: {old_baseline:.3f} -> {new_baseline:.3f}"
            )
            return True
        except Exception as e:
            self.logger.error(f"Baseline update failed for {metric_name}: {e}")
            return False
