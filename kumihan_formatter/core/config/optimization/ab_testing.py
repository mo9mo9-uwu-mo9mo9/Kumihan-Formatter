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
from typing import Any, List, Optional, Tuple, cast

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
    def ttest_ind(a: Any, b: Any, equal_var: bool = True) -> Any:
        """簡易t検定（scipyフォールバック）"""
        if not a or not b:
            return type("Result", (), {"statistic": 0, "pvalue": 1.0})

        mean_a = sum(a) / len(a)
        mean_b = sum(b) / len(b)
        var_a = sum((x - mean_a) ** 2 for x in a) / len(a)
        var_b = sum((x - mean_b) ** 2 for x in b) / len(b)

        pooled_std = ((var_a + var_b) / 2) ** 0.5
        if pooled_std == 0:
            return type("Result", (), {"statistic": 0, "pvalue": 1.0})

        t_stat = (mean_a - mean_b) / (pooled_std * (1 / len(a) + 1 / len(b)) ** 0.5)
        p_value = 0.05 if abs(t_stat) > 2 else 0.5  # 簡易推定

        return type("Result", (), {"statistic": t_stat, "pvalue": p_value})


class SimpleNumpy:
    """numpy未使用時のフォールバック数値計算"""

    @staticmethod
    def array(data: Any) -> Any:
        return data

    @staticmethod
    def std(data: Any) -> Any:
        try:
            return stdev(data) if len(data) > 1 else 0
        except (ValueError, TypeError):
            return 0

    @staticmethod
    def mean(data: Any) -> Any:
        return mean(data) if data else 0

    @staticmethod
    def sqrt(x: Any) -> Any:
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

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.scipy_available = SCIPY_AVAILABLE

        if not self.scipy_available:
            self.logger.warning(
                "scipy not available, using fallback statistical methods"
            )

    def calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """効果量Cohen's dを計算"""
        try:
            if not group1 or not group2:
                return 0.0

            mean1 = mean(group1)
            mean2 = mean(group2)

            if len(group1) == 1 and len(group2) == 1:
                return 0.0

            # プールされた標準偏差を計算
            std1 = stdev(group1) if len(group1) > 1 else 0
            std2 = stdev(group2) if len(group2) > 1 else 0

            pooled_std = math.sqrt(
                ((len(group1) - 1) * std1**2 + (len(group2) - 1) * std2**2)
                / (len(group1) + len(group2) - 2)
            )

            if pooled_std == 0:
                return 0.0

            return (mean1 - mean2) / pooled_std
        except (ValueError, TypeError, ZeroDivisionError) as e:
            self.logger.error(f"Error calculating Cohen's d: {e}")
            return 0.0

    def calculate_confidence_interval(
        self, data: List[float], confidence_level: float = 0.95
    ) -> Optional[Tuple[float, float]]:
        """信頼区間を計算"""
        try:
            if not data or len(data) < 2:
                return None

            if hasattr(self, "stats") and hasattr(self, "np"):
                return cast(
                    tuple[float, float],
                    stats.t.interval(
                        confidence_level,
                        len(data) - 1,
                        loc=np.mean(data),
                        scale=stats.sem(data),
                    ),
                )
            else:
                # フォールバック実装
                n = len(data)
                data_mean = mean(data)
                try:
                    sem = stdev(data) / math.sqrt(n)
                    h = sem * 1.96  # 95%信頼区間のためのt値近似
                    return (data_mean - h, data_mean + h)
                except (ValueError, TypeError):
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
                return max(int(50 / max(effect_size, 0.1)), 5)  # デフォルト
        except Exception as e:
            self.logger.error(f"Error calculating sample size: {e}")
            return 50  # デフォルト

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
                se_diff = math.sqrt(
                    np.var(group1) / len(group1) + np.var(group2) / len(group2)
                )
                ci_lower = diff - 1.96 * se_diff
                ci_upper = diff + 1.96 * se_diff

                # 検出力計算（事後）
                power = self._estimate_power(
                    len(group1), len(group2), effect_size, alpha
                )

                return StatisticalTestResult(
                    test_type=test_type,
                    statistic=float(statistic),
                    p_value=float(p_value),
                    significant=bool(p_value < alpha),
                    confidence_interval=(float(ci_lower), float(ci_upper)),
                    effect_size=effect_size,
                    power=power,
                )

            elif test_type == "mann_whitney" and self.scipy_available:
                # Mann-Whitney U検定
                statistic, p_value = stats.mannwhitneyu(
                    group1, group2, alternative="two-sided"
                )

                return StatisticalTestResult(
                    test_type=test_type,
                    statistic=float(statistic),
                    p_value=float(p_value),
                    significant=bool(p_value < alpha),
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

    def _estimate_power(
        self, n1: int, n2: int, effect_size: float, alpha: float
    ) -> float:
        """検出力を推定（事後分析）"""
        try:
            if effect_size == 0:
                return alpha  # 帰無仮説が真の場合

            # 簡易検出力推定（厳密でない近似）
            n_eff = min(n1, n2)
            if n_eff < 3:
                return 0.1  # 非常に小さいサンプル

            # 効果サイズとサンプルサイズに基づく簡易推定
            power_estimate = min(0.95, max(0.1, effect_size * math.sqrt(n_eff) * 0.5))
            return power_estimate
        except Exception as e:
            self.logger.error(f"Error estimating power: {e}")
            return 0.5  # デフォルト
