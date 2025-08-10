"""
A/B Testing Framework
====================

A/Bテスト関連クラスと統計テスト機能を提供します。

機能:
- A/Bテスト設定管理 (ABTestConfig)
- 統計テスト結果クラス (StatisticalTestResult, ABTestResult)
- 統計テストエンジン (StatisticalTestingEngine)
- 簡易統計計算ユーティリティ (SimpleStats, SimpleNumpy)
"""

import math
from dataclasses import dataclass
from statistics import mean, stdev
from typing import Any, List, Optional, Tuple

from kumihan_formatter.core.utilities.logger import get_logger

# scipyインポート（フォールバック機能付き）
try:
    import numpy as np
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class SimpleStats:
    """scipy未使用時のフォールバック統計計算"""

    @staticmethod
    def ttest_ind(a, b, equal_var=True):
        """簡易t検定（scipyフォールバック）"""
        if not a or not b:
            return type("Result", (), {"statistic": 0, "pvalue": 1.0})

        mean_a, mean_b = mean(a), mean(b)
        try:
            std_a, std_b = stdev(a), stdev(b)
            pooled_std = math.sqrt((std_a**2 + std_b**2) / 2)
            if pooled_std == 0:
                return type("Result", (), {"statistic": 0, "pvalue": 1.0})
            t_stat = abs(mean_a - mean_b) / pooled_std
            p_value = 0.01 if t_stat > 2.58 else (0.05 if t_stat > 1.96 else 1.0)
            return type("Result", (), {"statistic": t_stat, "pvalue": p_value})
        except (ValueError, ZeroDivisionError):
            return type("Result", (), {"statistic": 0, "pvalue": 1.0})


class SimpleNumpy:
    """numpy未使用時のフォールバック数値計算"""

    @staticmethod
    def array(data):
        return data

    @staticmethod
    def std(data):
        try:
            return stdev(data) if len(data) > 1 else 0
        except ValueError:
            return 0

    @staticmethod
    def mean(data):
        return mean(data) if data else 0

    @staticmethod
    def sqrt(x):
        return math.sqrt(x) if x >= 0 else 0


@dataclass
class ABTestConfig:
    """A/Bテスト設定（統計的検定強化版）"""

    parameter: str
    test_values: List[Any]
    sample_size: int = 10
    confidence_threshold: float = 0.95
    metric: str = "token_efficiency"

    # 統計的検定設定
    alpha: float = 0.05  # 有意水準
    power: float = 0.8  # 統計的検出力
    minimum_effect_size: float = 0.2  # 検出したい最小効果サイズ
    test_type: str = "t_test"  # "t_test", "mann_whitney"

    # 事前サンプルサイズ計算
    calculate_sample_size: bool = True


@dataclass
class StatisticalTestResult:
    """統計的検定結果"""

    test_type: str  # "t_test", "chi_square", "mann_whitney"
    statistic: float
    p_value: float
    significant: bool
    confidence_interval: Optional[Tuple[float, float]] = None
    effect_size: Optional[float] = None  # Cohen's d
    power: Optional[float] = None  # 統計的検出力


@dataclass
class ABTestResult:
    """A/Bテスト結果（統計的検定強化版）"""

    parameter: str
    winning_value: Any
    confidence: float
    improvement: float
    sample_count: int
    statistical_significance: bool

    # 統計的検定強化項目
    statistical_test: Optional[StatisticalTestResult] = None
    confidence_interval: Optional[Tuple[float, float]] = None
    effect_size: Optional[float] = None  # Cohen's d
    required_sample_size: Optional[int] = None
    statistical_power: Optional[float] = None


class StatisticalTestingEngine:
    """統計的検定エンジン（scipy統合/フォールバック対応）"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.scipy_available = SCIPY_AVAILABLE

        if not self.scipy_available:
            self.logger.warning("scipy not available, using fallback statistical methods")

    def calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """効果量Cohen's dを計算"""
        try:
            if not group1 or not group2:
                return 0.0

            if self.scipy_available:
                # scipyを使用した高精度計算
                mean1, mean2 = np.mean(group1), np.mean(group2)
                n1, n2 = len(group1), len(group2)

                if n1 == 1 and n2 == 1:
                    return 0.0

                # プールされた標準偏差を計算
                var1 = np.var(group1, ddof=1) if n1 > 1 else 0
                var2 = np.var(group2, ddof=1) if n2 > 1 else 0

                pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))

                if pooled_std == 0:
                    return 0.0

                cohens_d = (mean1 - mean2) / pooled_std
                return abs(cohens_d)
            else:
                # フォールバック実装
                mean1, mean2 = mean(group1), mean(group2)

                try:
                    std1 = stdev(group1) if len(group1) > 1 else 0
                    std2 = stdev(group2) if len(group2) > 1 else 0
                    pooled_std = math.sqrt((std1**2 + std2**2) / 2)

                    if pooled_std == 0:
                        return 0.0

                    return abs((mean1 - mean2) / pooled_std)
                except ValueError:
                    return 0.0

        except Exception as e:
            self.logger.error(f"Error calculating Cohen's d: {e}")
            return 0.0

    def calculate_confidence_interval(
        self, data: List[float], confidence_level: float = 0.95
    ) -> Optional[Tuple[float, float]]:
        """信頼区間を計算"""
        try:
            if not data or len(data) < 2:
                return None

            if self.scipy_available:
                # scipyを使用した正確な計算
                return tuple(
                    stats.t.interval(
                        confidence_level,
                        len(data) - 1,
                        loc=np.mean(data),
                        scale=stats.sem(data),
                    )
                )
            else:
                # フォールバック実装
                n = len(data)
                data_mean = mean(data)
                try:
                    sem = stdev(data) / math.sqrt(n)
                    h = sem * 1.96  # 95%信頼区間のためのt値近似
                    return (data_mean - h, data_mean + h)
                except ValueError:
                    return None

        except Exception as e:
            self.logger.error(f"Error calculating confidence interval: {e}")
            return None

    def calculate_required_sample_size(
        self, effect_size: float, alpha: float = 0.05, power: float = 0.8
    ) -> int:
        """必要サンプルサイズを計算"""
        try:
            if self.scipy_available:
                # scipyを使用した正確な計算
                from scipy.stats import norm

                z_alpha = norm.ppf(1 - alpha / 2)
                z_beta = norm.ppf(power)

                # Cohen's formula for two-sample t-test
                n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
                return max(int(math.ceil(n)), 5)  # 最小5サンプル
            else:
                # フォールバック実装（簡易計算）
                if effect_size <= 0:
                    return 50  # デフォルト

                # 簡易計算式
                n = 16 / (effect_size**2)  # 大まかな近似
                return max(int(math.ceil(n)), 10)

        except Exception as e:
            self.logger.error(f"Error calculating sample size: {e}")
            return 30  # フォールバック値

    def perform_statistical_test(
        self,
        group1: List[float],
        group2: List[float],
        test_type: str = "t_test",
        alpha: float = 0.05,
    ) -> StatisticalTestResult:
        """統計的検定を実行"""
        try:
            if not group1 or not group2:
                return StatisticalTestResult(
                    test_type=test_type, statistic=0.0, p_value=1.0, significant=False
                )

            if self.scipy_available and test_type == "t_test":
                # scipyを使用したt検定
                statistic, p_value = stats.ttest_ind(group1, group2, equal_var=False)

                # 効果量計算
                effect_size = self.calculate_cohens_d(group1, group2)

                # 信頼区間計算（差の信頼区間）
                diff = np.mean(group1) - np.mean(group2)
                se_diff = math.sqrt(np.var(group1) / len(group1) + np.var(group2) / len(group2))
                ci_lower = diff - 1.96 * se_diff
                ci_upper = diff + 1.96 * se_diff

                # 検出力計算（事後）
                power = self._estimate_power(len(group1), len(group2), effect_size, alpha)

                return StatisticalTestResult(
                    test_type=test_type,
                    statistic=float(statistic),
                    p_value=float(p_value),
                    significant=p_value < alpha,
                    confidence_interval=(ci_lower, ci_upper),
                    effect_size=effect_size,
                    power=power,
                )

            elif test_type == "mann_whitney" and self.scipy_available:
                # Mann-Whitney U検定
                statistic, p_value = stats.mannwhitneyu(group1, group2, alternative="two-sided")

                return StatisticalTestResult(
                    test_type=test_type,
                    statistic=float(statistic),
                    p_value=float(p_value),
                    significant=p_value < alpha,
                    effect_size=self.calculate_cohens_d(group1, group2),
                )

            else:
                # フォールバック実装
                stats_obj = SimpleStats()
                result = stats_obj.ttest_ind(group1, group2)

                return StatisticalTestResult(
                    test_type="t_test_fallback",
                    statistic=result.statistic,
                    p_value=result.pvalue,
                    significant=result.pvalue < alpha,
                    effect_size=self.calculate_cohens_d(group1, group2),
                )

        except Exception as e:
            self.logger.error(f"Error in statistical test: {e}")
            return StatisticalTestResult(
                test_type=test_type, statistic=0.0, p_value=1.0, significant=False
            )

    def _estimate_power(self, n1: int, n2: int, effect_size: float, alpha: float) -> float:
        """検出力を推定（事後分析）"""
        try:
            if effect_size == 0:
                return alpha  # 帰無仮説が真の場合

            # 簡易検出力計算
            n_harmonic = 2 / (1 / n1 + 1 / n2)
            ncp = effect_size * math.sqrt(n_harmonic / 2)

            # 正規近似による検出力計算
            z_alpha = 1.96  # alpha=0.05の場合
            power = (
                1 - stats.norm.cdf(z_alpha - ncp) + stats.norm.cdf(-z_alpha - ncp)
                if self.scipy_available
                else 0.8
            )

            return max(0.0, min(1.0, power))
        except Exception:
            return 0.8  # デフォルト値
