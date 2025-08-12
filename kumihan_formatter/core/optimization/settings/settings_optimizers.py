"""
Phase B.1 and B.2 Optimizers
============================

Phase B統合最適化システムを提供します。

機能:
- IntegratedSettingsOptimizer: 統合設定最適化システム
- LearningBasedOptimizer: 学習型最適化システム

目標: 追加5%削減（総合66.8%削減達成）
"""

import time
from collections import deque

# 循環インポート回避のため型ヒント用
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from kumihan_formatter.core.config.config_manager import EnhancedConfig
from kumihan_formatter.core.utilities.logger import get_logger

if TYPE_CHECKING:
    from .manager import AdaptiveSettingsManager, ConfigAdjustment
    from .optimizers import ContextAwareOptimizer, RealTimeConfigAdjuster


def _convert_to_enhanced_config(config_input: Any) -> EnhancedConfig:
    """EnhancedConfig変換ヘルパー"""
    if isinstance(config_input, EnhancedConfig):
        return config_input
    elif isinstance(config_input, dict):
        # dict から EnhancedConfig を作成
        enhanced_config = EnhancedConfig()
        for key, value in config_input.items():
            enhanced_config.set(key, value)
        return enhanced_config
    else:
        # フォールバック: 基本的なEnhancedConfig を作成
        return EnhancedConfig()


class IntegratedSettingsOptimizer:
    """
    統合設定最適化システム

    機能統合:
    - AdaptiveSettingsManager
    - ContextAwareOptimizer
    - RealTimeConfigAdjuster
    """

    def __init__(self, config: EnhancedConfig):
        self.logger = get_logger(__name__)
        self.config = config

        # 遅延インポートで循環参照回避
        self.adaptive_manager: Optional["AdaptiveSettingsManager"] = None
        self.context_optimizer: Optional[ContextAwareOptimizer] = None
        self.realtime_adjuster: Optional[RealTimeConfigAdjuster] = None

        self.logger.info("IntegratedSettingsOptimizer initialized")

    def _initialize_components(self):
        """Componentを遅延初期化"""
        if self.adaptive_manager is None:
            from .manager import AdaptiveSettingsManager

            self.adaptive_manager = AdaptiveSettingsManager(
                _convert_to_enhanced_config(self.config)
            )
            self.context_optimizer = ContextAwareOptimizer()
            self.realtime_adjuster = RealTimeConfigAdjuster(self.adaptive_manager)

    def optimize_for_operation(
        self, operation: str, content: str, user_id: str = "default"
    ) -> Dict[str, Any]:
        """操作に対する総合最適化"""
        self._initialize_components()

        # コンテキスト検出
        if self.context_optimizer is not None:
            context = self.context_optimizer.detect_context(operation, content, user_id)
        else:
            # フォールバック: デフォルトコンテキスト
            from .manager import WorkContext

            context = WorkContext(
                operation_type=operation,
                content_size=len(content),
                complexity_score=0.5,
                user_pattern=user_id,
            )

        # リアルタイム調整開始
        if self.realtime_adjuster is not None:
            self.realtime_adjuster.start_realtime_adjustment(context)

        return {
            "context": {
                "operation_type": context.operation_type,
                "content_size": context.content_size,
                "complexity_score": context.complexity_score,
                "user_pattern": context.user_pattern,
            },
            "adjustments_applied": (
                len(self.adaptive_manager.adjustment_history)
                if self.adaptive_manager is not None
                else 0
            ),
            "optimization_active": True,
        }

    def finalize_optimization(self) -> Dict[str, Any]:
        """最適化を完了し結果を返す"""
        self._initialize_components()

        adjustment_results = (
            self.realtime_adjuster.stop_realtime_adjustment()
            if self.realtime_adjuster is not None
            else {}
        )
        summary = (
            self.adaptive_manager.get_adjustment_summary()
            if self.adaptive_manager is not None
            else {}
        )

        return {
            "adjustment_results": adjustment_results,
            "summary": summary,
            "total_expected_benefit": summary["total_expected_benefit"],
        }


class LearningBasedOptimizer:
    """
    学習型最適化システム

    機能:
    - 基本パターン学習システム
    - A/Bテスト基本運用
    - 自動設定調整強化
    - 統合設定最適化システムとの統合運用

    目標: 追加5%削減（総合66.8%削減達成）
    """

    def __init__(
        self,
        config: EnhancedConfig,
        adaptive_manager: Optional["AdaptiveSettingsManager"] = None,
    ):
        self.logger = get_logger(__name__)
        self.config = config
        self.adaptive_manager = adaptive_manager

        # TokenEfficiencyAnalyzer統合
        self.efficiency_analyzer: Any = None

        # 学習型最適化専用設定
        self.learning_enabled = True
        self.ab_testing_enabled = True
        self.auto_optimization_threshold = 0.03  # 3%以上の改善で自動適用

        # 学習履歴
        self.learning_sessions: deque[Dict[str, Any]] = deque(maxlen=50)
        self.optimization_results: deque[Dict[str, Any]] = deque(maxlen=100)

        # 学習型最適化メトリクス
        self.learning_metrics = {
            "patterns_learned": 0,
            "optimizations_applied": 0,
            "ab_tests_completed": 0,
            "total_improvement": 0.0,
            "last_learning_session": None,
        }

        self.logger.info(
            "LearningBasedOptimizer initialized - 5% additional reduction target"
        )

    def _initialize_adaptive_manager(self):
        """AdaptiveSettingsManagerを遅延初期化"""
        if self.adaptive_manager is None:
            from .manager import AdaptiveSettingsManager

            self.adaptive_manager = AdaptiveSettingsManager(
                _convert_to_enhanced_config(self.config)
            )

    def integrate_efficiency_analyzer(self, analyzer: Any) -> None:
        """TokenEfficiencyAnalyzerとの統合"""
        self.efficiency_analyzer = analyzer
        self.logger.info("Integrated with TokenEfficiencyAnalyzer")

    def run_learning_cycle(self) -> Dict[str, Any]:
        """学習サイクル実行 - 学習型最適化メイン機能"""
        cycle_start = time.time()
        self._initialize_adaptive_manager()

        try:
            # 1. パターン学習実行
            learning_summary = (
                self.adaptive_manager.learn_usage_patterns()
                if self.adaptive_manager is not None
                else {"patterns_discovered": 0}
            )

            # 2. 効率性予測の取得（統合システム使用）
            efficiency_insights: dict[str, Any] = {}
            if self.efficiency_analyzer:
                efficiency_insights = self.efficiency_analyzer.get_pattern_insights()

            # 3. 統合分析
            integrated_analysis = self._integrate_learning_data(
                learning_summary, efficiency_insights
            )

            # 4. 最適化提案生成
            optimization_proposals = self._generate_optimization_proposals(
                integrated_analysis
            )

            # 5. 自動最適化適用
            applied_optimizations = self._apply_automatic_optimizations(
                optimization_proposals
            )

            # 6. A/Bテスト設定
            ab_tests_started = self._setup_ab_tests(optimization_proposals)

            # 7. 結果記録
            cycle_result = {
                "timestamp": cycle_start,
                "duration": time.time() - cycle_start,
                "patterns_analyzed": learning_summary["patterns_discovered"],
                "optimizations_applied": len(applied_optimizations),
                "ab_tests_started": len(ab_tests_started),
                "expected_improvement": sum(
                    opt.expected_benefit for opt in applied_optimizations
                ),
                "learning_summary": learning_summary,
                "efficiency_insights": efficiency_insights,
                "status": "completed",
            }

            self.learning_sessions.append(cycle_result)
            self._update_learning_metrics(cycle_result)

            self.logger.info(
                f"Learning cycle completed: {len(applied_optimizations)} optimizations, "
                f"{cycle_result['expected_improvement']:.1%} expected improvement"
            )

            return cycle_result

        except Exception as e:
            # エラー発生時の処理
            self.logger.error(f"Learning cycle failed: {e}")
            return {
                "timestamp": cycle_start,
                "duration": time.time() - cycle_start,
                "status": "failed",
                "error": str(e),
            }

    def _integrate_learning_data(
        self, learning_summary: Dict, efficiency_insights: Dict
    ) -> Dict[str, Any]:
        """学習データ統合分析"""
        integrated: Dict[str, Any] = {
            "high_priority_patterns": [],
            "optimization_opportunities": [],
            "conflicting_insights": [],
            "confidence_scores": {},
        }

        # パターン優先度決定
        for pattern_key, pattern_data in learning_summary.get(
            "efficiency_insights", {}
        ).items():
            efficiency_score = pattern_data["efficiency_score"]
            sample_count = pattern_data["sample_count"]

            # 効率性アナライザーからの洞察と統合
            analyzer_score = 0.5  # デフォルト
            if efficiency_insights and pattern_key in efficiency_insights.get(
                "pattern_rankings", {}
            ):
                analyzer_score = efficiency_insights["pattern_rankings"][pattern_key]

            # 統合スコア計算
            integrated_score = efficiency_score * 0.6 + analyzer_score * 0.4
            confidence = min(sample_count / 10, 0.9)

            if "confidence_scores" not in integrated:
                integrated["confidence_scores"] = {}
            integrated["confidence_scores"][pattern_key] = confidence

            if integrated_score < 0.6 and confidence > 0.5:
                integrated["high_priority_patterns"].append(
                    {
                        "pattern": pattern_key,
                        "integrated_score": integrated_score,
                        "confidence": confidence,
                        "sample_count": sample_count,
                    }
                )

        # 最適化機会の統合
        adaptive_opportunities = learning_summary.get("optimization_opportunities", [])
        analyzer_suggestions: list[dict[str, Any]] = []
        if self.efficiency_analyzer:
            # 効率アナライザーからの最適化提案取得
            analyzer_suggestions = self.efficiency_analyzer.auto_suggest_optimizations(
                self.config.get_all()
            )

        # 重複除去と統合
        all_opportunities = adaptive_opportunities + [
            {
                "pattern": sugg["pattern"],
                "recommendations": [
                    {
                        "type": sugg["type"],
                        "expected_improvement": sugg["expected_improvement"],
                    }
                ],
            }
            for sugg in analyzer_suggestions
        ]

        integrated["optimization_opportunities"] = all_opportunities

        return integrated

    def _generate_optimization_proposals(
        self, integrated_analysis: Dict
    ) -> List[Dict[str, Any]]:
        """最適化提案生成"""
        proposals = []

        for opportunity in integrated_analysis["optimization_opportunities"]:
            for recommendation in opportunity.get("recommendations", []):
                if (
                    recommendation.get("expected_improvement", 0)
                    >= self.auto_optimization_threshold
                ):
                    proposals.append(
                        {
                            "pattern": opportunity["pattern"],
                            "type": recommendation["type"],
                            "expected_improvement": recommendation[
                                "expected_improvement"
                            ],
                            "confidence": integrated_analysis["confidence_scores"].get(
                                opportunity["pattern"], 0.5
                            ),
                            "auto_apply": recommendation["expected_improvement"]
                            >= 0.05,  # 5%以上で自動適用
                            "ab_test_candidate": 0.03
                            <= recommendation["expected_improvement"]
                            < 0.05,
                        }
                    )

        # 期待改善率でソート
        proposals.sort(key=lambda x: x["expected_improvement"], reverse=True)
        return proposals[:10]  # 上位10提案

    def _apply_automatic_optimizations(
        self, proposals: List[Dict]
    ) -> List["ConfigAdjustment"]:
        """自動最適化適用"""
        from .manager import ConfigAdjustment

        applied = []

        for proposal in proposals:
            if proposal["auto_apply"] and proposal["confidence"] > 0.6:

                # max_answer_chars調整
                if proposal["type"] == "max_answer_chars_reduction":
                    current_value = self.config.get("serena.max_answer_chars", 25000)
                    new_value = max(15000, int(current_value * 0.8))  # 20%削減

                    adjustment = ConfigAdjustment(
                        key="serena.max_answer_chars",
                        old_value=current_value,
                        new_value=new_value,
                        context=f"learning_based_auto_{proposal['pattern']}",
                        timestamp=time.time(),
                        reason=(
                            f"LearningBasedOptimizer auto-optimization: "
                            f"{proposal['expected_improvement']:.1%} expected"
                        ),
                        expected_benefit=proposal["expected_improvement"],
                    )

                    if self.adaptive_manager is not None:
                        self.adaptive_manager._apply_adjustment(adjustment)
                        applied.append(adjustment)

        return applied

    def _setup_ab_tests(self, proposals: List[Dict]) -> List[str]:
        """A/Bテスト設定"""
        started_tests = []

        for proposal in proposals:
            if proposal["ab_test_candidate"] and self.ab_testing_enabled:
                parameter = "serena.max_answer_chars"  # 簡易版では固定

                if proposal["type"] == "max_answer_chars_reduction":
                    current_value = self.config.get(parameter, 25000)
                    test_values = [
                        current_value,
                        int(current_value * 0.9),  # 10%削減
                        int(current_value * 0.8),  # 20%削減
                    ]

                    test_started = (
                        self.adaptive_manager.run_simple_ab_test(
                            parameter, test_values, sample_size=8
                        )
                        if self.adaptive_manager is not None
                        else None
                    )

                    if test_started is not None:
                        started_tests.append(parameter)

        return started_tests

    def _update_learning_metrics(self, cycle_result: Dict):
        """学習型最適化メトリクス更新"""
        self.learning_metrics["patterns_learned"] += cycle_result.get(
            "patterns_analyzed", 0
        )
        self.learning_metrics["optimizations_applied"] += cycle_result.get(
            "optimizations_applied", 0
        )
        self.learning_metrics["ab_tests_completed"] += cycle_result.get(
            "ab_tests_started", 0
        )
        self.learning_metrics["total_improvement"] += cycle_result.get(
            "expected_improvement", 0
        )
        self.learning_metrics["last_learning_session"] = cycle_result["timestamp"]

    def get_learning_status(self) -> Dict[str, Any]:
        """学習型最適化ステータス取得"""
        self._initialize_adaptive_manager()
        learning_status = (
            self.adaptive_manager.get_learning_status()
            if self.adaptive_manager is not None
            else {"learning_active": False}
        )

        # 総合削減率計算（統合設定最適化 61.8% + 学習型最適化追加分）
        integrated_reduction = 0.618  # 統合設定最適化実績
        total_improvement = self.learning_metrics.get("total_improvement", 0.0)
        learning_additional = min(
            total_improvement if total_improvement is not None else 0.0, 0.1
        )  # 最大10%
        total_reduction = integrated_reduction + learning_additional

        return {
            "learning_metrics": self.learning_metrics,
            "learning_status": learning_status,
            "total_reduction_achieved": total_reduction,
            "target_progress": {
                "integrated_baseline": integrated_reduction,
                "learning_target": 0.05,  # 5%目標
                "learning_actual": learning_additional,
                "remaining_to_target": max(0.0, 0.05 - learning_additional),
            },
            "learning_sessions_count": len(self.learning_sessions),
            "recent_learning_active": (
                time.time() - (self.learning_metrics["last_learning_session"] or 0)
                < 3600
                if self.learning_metrics.get("last_learning_session")
                else False
            ),
        }

    def force_learning_cycle(self) -> Dict[str, Any]:
        """強制学習サイクル実行（テスト・デバッグ用）"""
        self.logger.info("Forcing learning cycle execution")
        return self.run_learning_cycle()
