"""
統計分析処理

AI効果測定の統計分析機能
"""

from typing import List, Tuple

from kumihan_formatter.core.utilities.logger import get_logger


class StatisticalAnalyzer:
    """統計分析システム"""

    def __init__(self) -> None:
        self.logger = get_logger(__name__ + ".StatisticalAnalyzer")

    def calculate_improvement(
        self, baseline: float, current: float
    ) -> Tuple[float, float]:
        """改善効果計算"""
        try:
            if baseline == 0.0:
                return 0.0, 0.0

            improvement = current - baseline
            improvement_percentage = (improvement / baseline) * 100.0

            return improvement, improvement_percentage
        except Exception as e:
            self.logger.error(f"Improvement calculation failed: {e}")
            return 0.0, 0.0

    def assess_statistical_significance(
        self,
        baseline_samples: List[float],
        current_samples: List[float],
        confidence_level: float = 0.95,
    ) -> Tuple[bool, float]:
        """統計的有意性評価"""
        try:
            if len(baseline_samples) < 2 or len(current_samples) < 2:
                return False, 0.0

            # t-test実行
            baseline_mean = sum(baseline_samples) / len(baseline_samples)
            current_mean = sum(current_samples) / len(current_samples)

            baseline_std = (
                sum((x - baseline_mean) ** 2 for x in baseline_samples)
                / (len(baseline_samples) - 1)
            ) ** 0.5
            current_std = (
                sum((x - current_mean) ** 2 for x in current_samples)
                / (len(current_samples) - 1)
            ) ** 0.5

            # 統合分散計算
            pooled_std = (
                (
                    (len(baseline_samples) - 1) * baseline_std**2
                    + (len(current_samples) - 1) * current_std**2
                )
                / (len(baseline_samples) + len(current_samples) - 2)
            ) ** 0.5

            # t統計量計算
            if pooled_std == 0:
                return baseline_mean != current_mean, 0.5

            # t値計算
            t_statistic = abs(baseline_mean - current_mean) / (
                pooled_std
                * ((1 / len(baseline_samples) + 1 / len(current_samples)) ** 0.5)
            )

            # 簡易的な有意性判定（t=2.0を閾値とする）
            is_significant = t_statistic > 2.0
            p_value = max(0.001, min(0.999, 0.5 - t_statistic * 0.1))  # 簡易p値近似

            return is_significant, p_value
        except Exception as e:
            self.logger.error(f"Statistical significance assessment failed: {e}")
            return False, 0.5

    def calculate_confidence_interval(
        self, samples: List[float], confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """信頼区間計算"""
        try:
            if len(samples) < 2:
                return 0.0, 0.0

            mean = sum(samples) / len(samples)
            std_dev = (
                sum((x - mean) ** 2 for x in samples) / (len(samples) - 1)
            ) ** 0.5

            # 簡易的な信頼区間計算（t分布近似）
            t_value = 2.0  # 95%信頼区間での近似t値
            margin_of_error = t_value * std_dev / (len(samples) ** 0.5)

            lower_bound = mean - margin_of_error
            upper_bound = mean + margin_of_error

            return lower_bound, upper_bound
        except Exception as e:
            self.logger.error(f"Confidence interval calculation failed: {e}")
            return 0.0, 0.0

    def detect_trend(self, time_series: List[Tuple[float, float]]) -> str:
        """トレンド検出（時刻, 値のペアリスト）"""
        try:
            if len(time_series) < 3:
                return "insufficient_data"

            # 線形回帰による傾き計算
            n = len(time_series)
            times = [t[0] for t in time_series]
            values = [t[1] for t in time_series]

            # 平均計算
            time_mean = sum(times) / n
            value_mean = sum(values) / n

            # 傾き計算
            numerator = sum(
                (times[i] - time_mean) * (values[i] - value_mean) for i in range(n)
            )
            denominator = sum((times[i] - time_mean) ** 2 for i in range(n))

            if denominator == 0:
                return "stable"

            slope = numerator / denominator

            # トレンド判定
            if slope > 0.1:
                return "increasing"
            elif slope < -0.1:
                return "decreasing"
            else:
                return "stable"
        except Exception as e:
            self.logger.error(f"Trend detection failed: {e}")
            return "unknown"
