"""メモリ使用量トレンド分析"""

from __future__ import annotations

from typing import Any, Dict, List

from kumihan_formatter.core.utilities.logger import get_logger
from ..snapshot import MemorySnapshot

logger = get_logger(__name__)


class MemoryTrendAnalyzer:
    """
    メモリ使用量トレンド分析クラス

    メモリ使用量の傾向とピーク分析を実行します。
    """

    def __init__(self) -> None:
        """トレンド分析器を初期化します。"""
        try:
            logger.info("MemoryTrendAnalyzer初期化完了")

        except Exception as e:
            logger.error(f"MemoryTrendAnalyzer初期化エラー: {str(e)}")
            raise

    def analyze_memory_trend(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """メモリトレンド分析"""
        try:
            if len(snapshots) < 2:
                return {}

            memory_values = [s.process_memory_mb for s in snapshots]

            # 線形回帰による傾向分析
            n = len(memory_values)
            x_mean = (n - 1) / 2
            y_mean = sum(memory_values) / n

            numerator = sum(
                (i - x_mean) * (memory_values[i] - y_mean) for i in range(n)
            )
            denominator = sum((i - x_mean) ** 2 for i in range(n))

            slope = numerator / denominator if denominator != 0 else 0

            # 変動係数
            std_dev = (sum((v - y_mean) ** 2 for v in memory_values) / n) ** 0.5
            cv = std_dev / y_mean if y_mean > 0 else 0

            # 成長率計算
            growth_rate = self._calculate_growth_rate(memory_values)

            return {
                "trend_slope_mb_per_snapshot": slope,
                "average_memory_mb": y_mean,
                "memory_volatility": cv,
                "standard_deviation_mb": std_dev,
                "trend_direction": (
                    "increasing"
                    if slope > 0.1
                    else "decreasing" if slope < -0.1 else "stable"
                ),
                "min_memory_mb": min(memory_values),
                "max_memory_mb": max(memory_values),
                "memory_range_mb": max(memory_values) - min(memory_values),
                "growth_rate_percent": growth_rate,
            }

        except Exception as e:
            logger.error(f"メモリトレンド分析エラー: {str(e)}")
            return {}

    def analyze_peaks(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """ピーク分析"""
        try:
            if len(snapshots) < 3:
                return {}

            memory_values = [s.process_memory_mb for s in snapshots]
            timestamps = [s.timestamp for s in snapshots]

            # ピーク検出
            peaks = []
            valleys = []

            for i in range(1, len(memory_values) - 1):
                # ピーク検出
                if (
                    memory_values[i] > memory_values[i - 1]
                    and memory_values[i] > memory_values[i + 1]
                ):
                    peaks.append(
                        {
                            "timestamp": timestamps[i],
                            "memory_mb": memory_values[i],
                            "index": i,
                        }
                    )

                # 谷検出
                if (
                    memory_values[i] < memory_values[i - 1]
                    and memory_values[i] < memory_values[i + 1]
                ):
                    valleys.append(
                        {
                            "timestamp": timestamps[i],
                            "memory_mb": memory_values[i],
                            "index": i,
                        }
                    )

            # 平均からの乖離分析
            avg_memory = sum(memory_values) / len(memory_values)
            significant_peaks = [p for p in peaks if p["memory_mb"] > avg_memory * 1.2]
            significant_valleys = [
                v for v in valleys if v["memory_mb"] < avg_memory * 0.8
            ]

            return {
                "total_peaks": len(peaks),
                "total_valleys": len(valleys),
                "significant_peaks": len(significant_peaks),
                "significant_valleys": len(significant_valleys),
                "peak_frequency": len(peaks) / len(snapshots) if snapshots else 0,
                "valley_frequency": len(valleys) / len(snapshots) if snapshots else 0,
                "avg_peak_height_mb": (
                    sum(p["memory_mb"] for p in peaks) / len(peaks) if peaks else 0
                ),
                "avg_valley_depth_mb": (
                    sum(v["memory_mb"] for v in valleys) / len(valleys)
                    if valleys
                    else 0
                ),
                "max_peak_mb": max((p["memory_mb"] for p in peaks), default=0),
                "min_valley_mb": min((v["memory_mb"] for v in valleys), default=0),
                "peak_valley_ratio": (
                    len(peaks) / len(valleys) if valleys else float("inf")
                ),
            }

        except Exception as e:
            logger.error(f"ピーク分析エラー: {str(e)}")
            return {}

    def analyze_memory_stability(
        self, snapshots: List[MemorySnapshot]
    ) -> Dict[str, Any]:
        """メモリ安定性分析"""
        try:
            if len(snapshots) < 5:
                return {}

            memory_values = [s.process_memory_mb for s in snapshots]

            # 移動平均計算
            window_size = min(5, len(memory_values) // 2)
            moving_avg = self._calculate_moving_average(memory_values, window_size)

            # 安定性指標計算
            stability_score = self._calculate_stability_score(memory_values, moving_avg)

            # 振動分析
            oscillation = self._analyze_oscillation(memory_values)

            return {
                "stability_score": stability_score,
                "moving_average_mb": moving_avg[-1] if moving_avg else 0,
                "oscillation_amplitude_mb": oscillation["amplitude"],
                "oscillation_frequency": oscillation["frequency"],
                "is_stable": stability_score > 0.7,
                "stability_level": self._get_stability_level(stability_score),
            }

        except Exception as e:
            logger.error(f"メモリ安定性分析エラー: {str(e)}")
            return {}

    def _calculate_growth_rate(self, values: List[float]) -> float:
        """成長率を計算します（%）"""
        try:
            if len(values) < 2:
                return 0.0

            first_value = values[0]
            last_value = values[-1]

            if first_value <= 0:
                return 0.0

            return ((last_value - first_value) / first_value) * 100

        except Exception as e:
            logger.error(f"成長率計算エラー: {str(e)}")
            return 0.0

    def _calculate_moving_average(
        self, values: List[float], window_size: int
    ) -> List[float]:
        """移動平均を計算します"""
        try:
            moving_avg = []

            for i in range(len(values)):
                start_idx = max(0, i - window_size + 1)
                end_idx = i + 1
                window_values = values[start_idx:end_idx]
                avg = sum(window_values) / len(window_values)
                moving_avg.append(avg)

            return moving_avg

        except Exception as e:
            logger.error(f"移動平均計算エラー: {str(e)}")
            return []

    def _calculate_stability_score(
        self, values: List[float], moving_avg: List[float]
    ) -> float:
        """安定性スコアを計算します（0-1）"""
        try:
            if not values or not moving_avg or len(values) != len(moving_avg):
                return 0.0

            # 移動平均からの平均絶対偏差
            mean_absolute_deviation = sum(
                abs(values[i] - moving_avg[i]) for i in range(len(values))
            ) / len(values)

            # 平均値に対する相対的な安定性
            avg_value = sum(values) / len(values)
            if avg_value <= 0:
                return 0.0

            relative_deviation = mean_absolute_deviation / avg_value
            stability_score = max(0.0, 1.0 - relative_deviation)

            return min(stability_score, 1.0)

        except Exception as e:
            logger.error(f"安定性スコア計算エラー: {str(e)}")
            return 0.0

    def _analyze_oscillation(self, values: List[float]) -> Dict[str, float]:
        """振動分析"""
        try:
            if len(values) < 3:
                return {"amplitude": 0.0, "frequency": 0.0}

            # 簡易振動分析
            direction_changes = 0

            for i in range(1, len(values) - 1):
                if (values[i] > values[i - 1] and values[i + 1] < values[i]) or (
                    values[i] < values[i - 1] and values[i + 1] > values[i]
                ):
                    direction_changes += 1

            frequency = direction_changes / (len(values) - 2) if len(values) > 2 else 0

            # 振幅計算（最大値と最小値の差）
            amplitude = max(values) - min(values) if values else 0.0

            return {
                "amplitude": amplitude,
                "frequency": frequency,
            }

        except Exception as e:
            logger.error(f"振動分析エラー: {str(e)}")
            return {"amplitude": 0.0, "frequency": 0.0}

    def _get_stability_level(self, stability_score: float) -> str:
        """安定性レベルを取得します"""
        try:
            if stability_score >= 0.8:
                return "very_stable"
            elif stability_score >= 0.6:
                return "stable"
            elif stability_score >= 0.4:
                return "moderately_stable"
            elif stability_score >= 0.2:
                return "unstable"
            else:
                return "very_unstable"

        except Exception as e:
            logger.error(f"安定性レベル取得エラー: {str(e)}")
            return "unknown"
