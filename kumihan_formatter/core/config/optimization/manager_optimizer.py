"""
Adaptive Settings Manager Optimizer Components
==============================================

AI最適化、学習システム、A/Bテストなどの高度な最適化機能を提供します。

機能:
- AI駆動型最適化システム
- 学習型調整システム
- A/Bテスト自動実行
- パフォーマンス測定・分析
"""

import time
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast

from kumihan_formatter.core.utilities.logger import get_logger

if TYPE_CHECKING:
    from .manager_core import AdaptiveSettingsManagerCore, ConfigAdjustment, WorkContext


class AdaptiveSettingsManagerOptimizer:
    """
    動的設定調整システムの最適化機能クラス

    機能:
    - AI駆動型最適化
    - 学習型調整システム
    - A/Bテスト管理
    - パフォーマンス分析
    """

    def __init__(self, core_manager: "AdaptiveSettingsManagerCore"):
        self.logger = get_logger(__name__)
        self.core = core_manager

        # A/Bテスト管理
        self.active_tests: Dict[str, Any] = {}  # ABTestConfig型は遅延インポート
        self.test_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        self.logger.info("AdaptiveSettingsManagerOptimizer initialized")

    def apply_ai_optimizations(self, context: "WorkContext") -> List[Any]:
        """
        AI駆動型最適化システムを適用 - Issue #804 中核実装

        Args:
            context: 作業コンテキスト

        Returns:
            適用された最適化調整のリスト
        """
        ai_adjustments: List[Any] = []

        # 1. ファイルサイズ制限最適化
        file_size_adjustments = self._apply_file_size_optimizations(context)
        ai_adjustments.extend(file_size_adjustments)

        # 2. 並列制御最適化
        concurrent_adjustments = self._apply_concurrent_optimizations(context)
        ai_adjustments.extend(concurrent_adjustments)

        # 3. Token使用量最適化
        token_adjustments = self._apply_token_optimizations(context)
        ai_adjustments.extend(token_adjustments)

        # 統合効果レポート
        if ai_adjustments:
            total_expected_benefit = sum(
                getattr(adj, "expected_benefit", 0.0) for adj in ai_adjustments
            )
            self.logger.info(
                f"AI optimizations applied: {len(ai_adjustments)} adjustments, "
                f"expected total benefit: {total_expected_benefit:.1%}"
            )

        return ai_adjustments

    def _apply_file_size_optimizations(self, context: "WorkContext") -> List[Any]:
        """ファイルサイズ制限最適化を適用"""
        adjustments: List[Any] = []

        # 動的サイズ制限調整
        if (
            self.core.file_size_optimizer
            and self.core.file_size_optimizer.adjust_limits_dynamically(context)
        ):
            # サイズ制限が調整された場合、関連する設定も更新（Serena削除により無効化）
            pass  # 削除: Serena未使用のため処理なし

        return adjustments

    def _apply_concurrent_optimizations(self, context: "WorkContext") -> List[Any]:
        """並列処理制限最適化を適用"""
        adjustments: List[Any] = []

        # リアルタイム性能指標を取得（簡易版）
        if not self.core.concurrent_limiter:
            return []
        concurrency_stats = self.core.concurrent_limiter.get_concurrency_statistics()
        performance_metrics = {
            "average_response_time": 5.0,  # 実装時に実際の指標に置換
            "resource_usage_percent": 60,  # 実装時に実際の指標に置換
        }

        # 性能指標に基づく調整
        old_limit = concurrency_stats["max_concurrent_calls"]
        if self.core.concurrent_limiter:
            self.core.concurrent_limiter.adjust_limits_based_on_performance(
                performance_metrics
            )
            new_stats = self.core.concurrent_limiter.get_concurrency_statistics()
            new_limit = new_stats["max_concurrent_calls"]
        else:
            new_limit = old_limit

        if old_limit != new_limit:
            # 並列制御設定の調整を記録
            from .manager_core import ConfigAdjustment

            adjustment = ConfigAdjustment(
                key="optimization.max_concurrent_tools",
                old_value=old_limit,
                new_value=new_limit,
                context=f"ai_concurrent_optimization_{context.operation_type}",
                timestamp=time.time(),
                reason="Concurrent control adjustment based on performance metrics",
                expected_benefit=0.12,  # 並列制御による効率改善
            )
            adjustments.append(adjustment)

            # 設定の実際の更新
            self.core.config.set(
                "optimization.max_concurrent_tools", new_limit, "ai_optimizer"
            )

        return adjustments

    def _apply_token_optimizations(self, context: "WorkContext") -> List[Any]:
        """Token使用量最適化を適用"""
        adjustments: List[Any] = []

        # コンテキストに基づくToken使用量の記録と分析
        estimated_input_tokens = int(context.content_size * 0.25)  # 概算
        estimated_output_tokens = int(
            context.complexity_score * 2000
        )  # 複雑性ベース概算

        # Token使用量を記録
        if not self.core.token_analyzer:
            return []
        analysis_result = self.core.token_analyzer.record_token_usage(
            operation_type=context.operation_type,
            input_tokens=estimated_input_tokens,
            output_tokens=estimated_output_tokens,
            context=context,
        )

        # 最適化提案があるかチェック
        if "optimization_suggestions" in analysis_result:
            for suggestion in analysis_result["optimization_suggestions"]:
                if (
                    suggestion["priority"] == "high"
                    and suggestion.get("estimated_total_reduction", 0) > 0.15
                ):
                    # 高優先度で15%以上の削減期待値がある場合に適用
                    for action in suggestion["actions"]:
                        if action["action"] == "apply_file_size_limits":
                            # max_answer_charsをより厳格に設定（Serena削除により無効化）
                            pass  # 削除: Serena未使用のため処理なし

        # 効率性スコアが低い場合の追加最適化
        efficiency_score = analysis_result.get("efficiency_score", 1.0)
        if efficiency_score < 0.6:
            # 低効率の場合、より保守的な設定を適用
            current_recursion = self.core.config.get(
                "performance.max_recursion_depth", 50
            )
            if current_recursion > 30:
                optimized_recursion = max(30, int(current_recursion * 0.8))
                from .manager_core import ConfigAdjustment

                adjustment = ConfigAdjustment(
                    key="performance.max_recursion_depth",
                    old_value=current_recursion,
                    new_value=optimized_recursion,
                    context=f"ai_efficiency_optimization_{context.operation_type}",
                    timestamp=time.time(),
                    reason=f"Low efficiency optimization (score: {efficiency_score:.2f})",
                    expected_benefit=0.08,
                )
                adjustments.append(adjustment)

        return adjustments

    def get_ai_optimization_summary(self) -> Dict[str, Any]:
        """AI最適化システムの総合サマリーを取得 - Issue #804"""
        self.core._initialize_components()

        return {
            "file_size_optimization": (
                self.core.file_size_optimizer.get_optimization_statistics()
                if self.core.file_size_optimizer
                else {}
            ),
            "concurrent_control": (
                self.core.concurrent_limiter.get_concurrency_statistics()
                if self.core.concurrent_limiter
                else {}
            ),
            "token_analysis": (
                self.core.token_analyzer.get_usage_analytics()
                if self.core.token_analyzer
                else {}
            ),
            "integration_status": {
                "total_ai_adjustments": len(
                    [
                        adj
                        for adj in self.core.adjustment_history
                        if "ai_" in adj.context
                    ]
                ),
                "expected_total_benefit": sum(
                    adj.expected_benefit
                    for adj in self.core.adjustment_history
                    if "ai_" in adj.context
                ),
                "last_optimization": max(
                    (
                        adj.timestamp
                        for adj in self.core.adjustment_history
                        if "ai_" in adj.context
                    ),
                    default=0,
                ),
            },
            "system_health": {
                "file_optimizer_active": self.core.file_size_optimizer is not None,
                "concurrent_limiter_active": self.core.concurrent_limiter is not None,
                "token_analyzer_active": self.core.token_analyzer is not None,
                "integration_complete": all(
                    [
                        self.core.file_size_optimizer is not None,
                        self.core.concurrent_limiter is not None,
                        self.core.token_analyzer is not None,
                    ]
                ),
            },
        }

    # ================================
    # A/Bテスト関連メソッド群
    # ================================

    def start_ab_test(
        self, parameter: str, test_values: List[Any], sample_size: int = 10
    ) -> Optional[str]:
        """A/Bテストを開始"""

        if parameter in self.active_tests:
            self.logger.warning(f"A/B test already running for {parameter}")
            return None

        from .ab_testing import ABTestConfig

        test_config = ABTestConfig(
            parameter=parameter,
            test_values=test_values,
            sample_size=sample_size,
            confidence_threshold=0.95,
        )

        test_id = f"{parameter}_{int(time.time())}"
        self.active_tests[test_id] = {
            "config": test_config,
            "start_time": time.time(),
            "results": [],
            "current_value_index": 0,
        }

        self.logger.info(f"Started A/B test: {test_id} with values: {test_values}")
        return test_id

    def record_ab_test_result(
        self, test_id: str, metric_value: float, context: Optional["WorkContext"] = None
    ) -> bool:
        """A/Bテスト結果を記録"""
        if test_id not in self.active_tests:
            return False

        test_data = self.active_tests[test_id]
        test_config = test_data["config"]

        # 結果記録
        result_entry = {
            "timestamp": time.time(),
            "value_index": test_data["current_value_index"],
            "test_value": test_config.test_values[test_data["current_value_index"]],
            "metric_value": metric_value,
            "context_size": context.content_size if context else 0,
        }

        test_data["results"].append(result_entry)

        # サンプルサイズチェック
        current_sample_count = len(
            [
                r
                for r in test_data["results"]
                if r["value_index"] == test_data["current_value_index"]
            ]
        )

        if current_sample_count >= test_config.sample_size:
            # 次の値に移行
            test_data["current_value_index"] += 1
            if test_data["current_value_index"] >= len(test_config.test_values):
                # テスト完了
                self._finalize_ab_test(test_id)

        return True

    def _finalize_ab_test(self, test_id: str) -> None:
        """A/Bテストを完了し結果を分析"""
        if test_id not in self.active_tests:
            return

        test_data = self.active_tests[test_id]
        test_config = test_data["config"]

        # 統計分析実行
        value_groups = defaultdict(list)
        for result in test_data["results"]:
            value_groups[result["value_index"]].append(result["metric_value"])

        # 最良値を特定
        best_value_index = 0
        best_performance = 0

        for value_index, metrics in value_groups.items():
            avg_performance = sum(metrics) / len(metrics) if metrics else 0
            if avg_performance > best_performance:
                best_performance = avg_performance
                best_value_index = value_index

        # 結果記録
        from .ab_testing import ABTestResult

        result = ABTestResult(
            parameter=test_config.parameter,
            winning_value=test_config.test_values[best_value_index],
            confidence=0.95,  # 簡易版
            improvement=0.1,  # 簡易版
            sample_count=len(test_data["results"]),
            statistical_significance=len(test_data["results"])
            >= test_config.sample_size,
        )

        self.test_results[test_config.parameter].append(result.__dict__)

        # アクティブテストから削除
        del self.active_tests[test_id]

        self.logger.info(
            f"A/B test completed: {test_config.parameter}, winning value: {result.winning_value}"
        )

    def run_simple_ab_test(
        self, parameter: str, test_values: List[Any], sample_size: int = 8
    ) -> Optional[str]:
        """簡易A/Bテスト実行（Phase B.2用）"""
        return self.start_ab_test(parameter, test_values, sample_size)

    def get_ab_test_results(self, parameter: str) -> List[Dict[str, Any]]:
        """A/Bテスト結果を取得"""
        return self.test_results.get(parameter, [])

    # ================================
    # 学習システム関連メソッド群
    # ================================

    def learn_usage_patterns(self) -> Dict[str, Any]:
        """使用パターンを学習し、効率性洞察を生成"""
        learning_summary: Dict[str, Any] = {
            "patterns_discovered": 0,
            "efficiency_insights": {},
            "optimization_opportunities": [],
            "learning_timestamp": time.time(),
        }

        # コンテキストパターン分析
        for pattern_key, pattern_data in self.core.context_patterns.items():
            if pattern_data["count"] >= 3:  # 最小3回の観測
                # 効率性スコア計算
                efficiency_score = self._calculate_pattern_efficiency(pattern_data)

                if "efficiency_insights" not in learning_summary:
                    learning_summary["efficiency_insights"] = {}
                learning_summary["efficiency_insights"][pattern_key] = {
                    "efficiency_score": efficiency_score,
                    "sample_count": pattern_data["count"],
                    "avg_size": pattern_data["avg_size"],
                    "avg_complexity": pattern_data["avg_complexity"],
                }

                # 最適化機会の特定
                if efficiency_score < 0.7:
                    learning_summary["optimization_opportunities"].append(
                        {
                            "pattern": pattern_key,
                            "current_efficiency": efficiency_score,
                            "recommendations": [
                                {
                                    "type": "max_answer_chars_reduction",
                                    "expected_improvement": (0.7 - efficiency_score)
                                    * 0.5,
                                }
                            ],
                        }
                    )

        learning_summary["patterns_discovered"] = len(
            learning_summary["efficiency_insights"]
        )
        return learning_summary

    def _calculate_pattern_efficiency(self, pattern_data: Dict[str, Any]) -> float:
        """パターン効率性を計算"""
        # 簡易効率性計算
        base_efficiency = 0.8

        # サイズ効率性（小さいほど良い）
        size_factor = max(0, 1 - pattern_data["avg_size"] / 100000)
        complexity_factor = max(0, 1 - pattern_data["avg_complexity"])

        efficiency = base_efficiency * 0.4 + size_factor * 0.3 + complexity_factor * 0.3
        return cast(float, max(0.0, min(1.0, efficiency)))

    def apply_learned_optimizations(self) -> List[Any]:
        """学習した最適化を適用"""
        applied_adjustments: List[Any] = []

        learning_summary = self.learn_usage_patterns()

        for opportunity in learning_summary["optimization_opportunities"]:
            for recommendation in opportunity["recommendations"]:
                if recommendation["expected_improvement"] > 0.05:  # 5%以上の改善期待値
                    adjustment = self._create_learned_adjustment(
                        opportunity["pattern"], recommendation
                    )
                    if adjustment:
                        self.core._apply_adjustment(adjustment)
                        applied_adjustments.append(adjustment)

        return applied_adjustments

    def _create_learned_adjustment(
        self, pattern: str, recommendation: Dict[str, Any]
    ) -> Optional["ConfigAdjustment"]:
        """学習基づく調整を作成（Serena削除により無効化）"""
        # if recommendation["type"] == "max_answer_chars_reduction":
        #     current_value = self.core.config.get(
        #         "serena.max_answer_chars", 25000
        #     )  # 削除: Serena未使用
        #     reduction_rate = min(recommendation["expected_improvement"], 0.3)
        #     new_value = max(15000, int(current_value * (1 - reduction_rate)))

        #     if new_value != current_value:
        #         from .manager_core import ConfigAdjustment
        #         return ConfigAdjustment(
        #             key="serena.max_answer_chars",
        #             old_value=current_value,
        #             new_value=new_value,
        #             context=f"learned_optimization_{pattern}",
        #             timestamp=time.time(),
        #             reason=f"Pattern learning: {pattern}",
        #             expected_benefit=recommendation["expected_improvement"],
        #         )
        return None  # Serena削除により常にNoneを返す

    def get_learning_status(self) -> Dict[str, Any]:
        """学習システムの状況を取得"""
        total_patterns = len(self.core.context_patterns)
        learned_patterns = sum(
            1
            for pattern in self.core.context_patterns.values()
            if pattern["count"] >= 3
        )

        recent_adjustments = [
            adj for adj in self.core.adjustment_history if "learned_" in adj.context
        ]

        return {
            "total_context_patterns": total_patterns,
            "learned_patterns": learned_patterns,
            "learning_coverage": (
                learned_patterns / total_patterns if total_patterns > 0 else 0.0
            ),
            "recent_learned_adjustments": len(recent_adjustments),
            "total_learned_benefit": sum(
                adj.expected_benefit for adj in recent_adjustments
            ),
            "learning_active": total_patterns > 0,
        }
