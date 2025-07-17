"""
ベンチマーク 回帰分析

パフォーマンス回帰の検出・分析
Issue #492 Phase 5A - benchmark_analyzer.py分割
"""

import statistics
from typing import Any, Union

from ..utilities.logger import get_logger
from .benchmark_types import PERFORMANCE_THRESHOLDS, BenchmarkResult, RegressionAnalysis


class BenchmarkRegressionAnalyzer:
    """ベンチマーク回帰分析器

    責任:
    - パフォーマンス回帰の検出
    - 回帰分析結果の生成
    - 深刻度評価
    - 回帰詳細情報の提供
    """

    def __init__(self) -> None:
        """回帰分析器を初期化"""
        self.logger = get_logger(__name__)

    def analyze_regression(
        self,
        current_results: dict[str, BenchmarkResult],
        baseline_results: dict[str, BenchmarkResult],
    ) -> dict[str, Any]:
        """パフォーマンス回帰を分析

        Args:
            current_results: 現在の結果
            baseline_results: ベースライン結果

        Returns:
            回帰分析結果
        """
        self.logger.info("パフォーマンス回帰分析開始")

        regressions = []
        improvements = []

        for name, current in current_results.items():
            if name not in baseline_results:
                self.logger.warning(f"ベースラインに存在しないベンチマーク: {name}")
                continue

            baseline = baseline_results[name]
            regression_analysis = self.analyze_single_regression(current, baseline)

            if regression_analysis.is_regression:
                regressions.append(regression_analysis)
                self.logger.warning(
                    f"回帰検出: {name}, 性能悪化={regression_analysis.performance_change_percent:.1f}%"
                )
            elif regression_analysis.performance_change_percent < -5.0:  # 5%以上の改善
                improvements.append(regression_analysis)
                self.logger.info(
                    f"性能改善: {name}, 改善={abs(regression_analysis.performance_change_percent):.1f}%"
                )

        # 総合評価
        overall_regression = len(regressions) > 0
        severity = self.calculate_overall_severity(regressions)

        analysis = {
            "overall_regression": overall_regression,
            "severity": severity,
            "regressions_detected": regressions,
            "improvements_detected": improvements,
            "summary": {
                "total_benchmarks_compared": len(current_results),
                "regressions_count": len(regressions),
                "improvements_count": len(improvements),
                "overall_performance_change": self.calculate_overall_performance_change(
                    current_results, baseline_results
                ),
            },
        }

        self.logger.info(
            f"回帰分析完了: {len(regressions)}個の回帰, {len(improvements)}個の改善"
        )
        return analysis

    def analyze_single_regression(
        self, current: BenchmarkResult, baseline: BenchmarkResult
    ) -> RegressionAnalysis:
        """単一ベンチマークの回帰分析

        Args:
            current: 現在の結果
            baseline: ベースライン結果

        Returns:
            回帰分析結果
        """
        performance_change_percent = (
            (current.avg_time - baseline.avg_time) / baseline.avg_time * 100
        )

        is_regression = (
            performance_change_percent
            > PERFORMANCE_THRESHOLDS["regression_threshold_percent"]
        )

        # 深刻度評価
        severity = self._calculate_severity(performance_change_percent)

        # メモリ変化計算
        memory_change_percent = self._calculate_memory_change(current, baseline)

        return RegressionAnalysis(
            benchmark_name=current.name,
            baseline_avg_time=baseline.avg_time,
            current_avg_time=current.avg_time,
            performance_change_percent=performance_change_percent,
            is_regression=is_regression,
            severity=severity,
            memory_change_percent=memory_change_percent,
        )

    def calculate_overall_performance_change(
        self,
        current_results: dict[str, BenchmarkResult],
        baseline_results: dict[str, BenchmarkResult],
    ) -> float:
        """全体のパフォーマンス変化を計算

        Args:
            current_results: 現在の結果
            baseline_results: ベースライン結果

        Returns:
            全体のパフォーマンス変化（パーセント）
        """
        changes = []

        for name, current in current_results.items():
            if name in baseline_results:
                baseline = baseline_results[name]
                change = (
                    (current.avg_time - baseline.avg_time) / baseline.avg_time * 100
                )
                changes.append(change)

        return statistics.mean(changes) if changes else 0.0

    def calculate_overall_severity(self, regressions: list[RegressionAnalysis]) -> str:
        """全体の深刻度を計算

        Args:
            regressions: 回帰分析結果のリスト

        Returns:
            全体の深刻度
        """
        if not regressions:
            return "none"

        severe_count = sum(1 for r in regressions if r.severity == "severe")
        moderate_count = sum(1 for r in regressions if r.severity == "moderate")

        if severe_count > 0:
            return "severe"
        elif moderate_count > 0:
            return "moderate"
        else:
            return "minor"

    def _calculate_severity(self, performance_change_percent: float) -> str:
        """パフォーマンス変化の深刻度を計算

        Args:
            performance_change_percent: パフォーマンス変化率

        Returns:
            深刻度レベル
        """
        if (
            performance_change_percent
            > PERFORMANCE_THRESHOLDS["severe_regression_percent"]
        ):
            return "severe"
        elif (
            performance_change_percent
            > PERFORMANCE_THRESHOLDS["regression_threshold_percent"]
        ):
            if performance_change_percent > 20.0:
                return "moderate"
            else:
                return "minor"
        else:
            return "none"

    def _calculate_memory_change(
        self, current: BenchmarkResult, baseline: BenchmarkResult
    ) -> Union[float, None]:
        """メモリ変化率を計算

        Args:
            current: 現在の結果
            baseline: ベースライン結果

        Returns:
            メモリ変化率（パーセント）
        """
        if not (
            current.memory_usage.get("peak_mb") and baseline.memory_usage.get("peak_mb")
        ):
            return None

        current_memory = current.memory_usage["peak_mb"]
        baseline_memory = baseline.memory_usage["peak_mb"]

        return (current_memory - baseline_memory) / baseline_memory * 100
