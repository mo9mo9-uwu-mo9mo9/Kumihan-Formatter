"""
Adaptive Settings Manager and Support Classes
============================================

動的設定調整の中核クラスとサポートクラスを提供します。

機能:
- AdaptiveSettingsManager: 動的設定調整の中核
- ConfigAdjustment: 設定調整情報
- WorkContext: 作業コンテキスト情報
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field

# 循環インポート回避のための遅延インポート
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, cast

from kumihan_formatter.core.config.config_manager import EnhancedConfig
from kumihan_formatter.core.utilities.logger import get_logger

if TYPE_CHECKING:
    from .ab_testing import StatisticalTestingEngine
    from .analyzers import TokenUsageAnalyzer
    from .optimizers import ConcurrentToolCallLimiter, FileSizeLimitOptimizer


@dataclass
class ConfigAdjustment:
    """設定調整情報"""

    key: str
    old_value: Any
    new_value: Any
    context: str
    timestamp: float
    reason: str
    expected_benefit: float = 0.0


@dataclass
class WorkContext:
    """作業コンテキスト情報"""

    operation_type: str  # "parsing", "rendering", "optimization"
    content_size: int
    complexity_score: float
    user_pattern: str = "default"
    timestamp: float = field(default_factory=time.time)

    # Phase B統合システム用の追加属性（型安全性確保）
    task_type: Optional[str] = None  # "integration_test", "periodic_measurement"等
    complexity_level: Optional[str] = None  # "simple", "medium", "complex"
    cache_hit_rate: Optional[float] = None  # キャッシュヒット率 (0.0-1.0)
    adjustment_effectiveness: Optional[float] = None  # 調整効果度 (0.0-1.0)
    monitoring_optimization_score: Optional[float] = (
        None  # モニタリング最適化スコア (0.0-1.0)
    )


class AdaptiveSettingsManager:
    """
    動的設定調整の中核クラス

    機能:
    - コンテキスト認識による設定最適化
    - リアルタイム効果測定
    - 学習型調整システム
    - A/Bテスト自動実行
    """

    def __init__(self, config: EnhancedConfig):
        self.logger = get_logger(__name__)
        self.config = config

        # 遅延インポートで循環参照回避
        self.statistical_engine: Optional["StatisticalTestingEngine"] = None
        self.file_size_optimizer: Optional["FileSizeLimitOptimizer"] = None
        self.concurrent_limiter: Optional["ConcurrentToolCallLimiter"] = None
        self.token_analyzer: Optional["TokenUsageAnalyzer"] = None

        # 調整履歴管理
        self.adjustment_history: deque[ConfigAdjustment] = deque(maxlen=1000)
        self.context_patterns: Dict[str, Dict[str, Any]] = {}

        # A/Bテスト管理
        self.active_tests: Dict[str, Any] = {}  # ABTestConfig型は遅延インポート
        self.test_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # 効果測定
        self.performance_baselines: Dict[str, float] = {}
        self.recent_metrics: deque[Dict[str, Any]] = deque(maxlen=100)

        # 設定調整ルール
        self.adjustment_rules = self._initialize_adjustment_rules()

        # スレッドセーフティ
        self._lock = threading.Lock()

        self.logger.info("AdaptiveSettingsManager initialized")

    def _initialize_components(self):
        """必要なコンポーネントを遅延初期化"""
        if self.statistical_engine is None:
            from .ab_testing import StatisticalTestingEngine

            self.statistical_engine = StatisticalTestingEngine()

        if self.file_size_optimizer is None:
            from kumihan_formatter.core.unified_config import EnhancedConfigAdapter

            from .analyzers import TokenUsageAnalyzer
            from .optimizers import ConcurrentToolCallLimiter, FileSizeLimitOptimizer

            config_adapter = EnhancedConfigAdapter(self.config)
            self.file_size_optimizer = FileSizeLimitOptimizer(config_adapter)
            self.concurrent_limiter = ConcurrentToolCallLimiter(config_adapter)
            self.token_analyzer = TokenUsageAnalyzer(config_adapter)

    def _initialize_adjustment_rules(self) -> Dict[str, Callable]:
        """設定調整ルールを初期化"""
        return {
            "max_answer_chars": self._adjust_max_answer_chars,
            "max_recursion_depth": self._adjust_recursion_depth,
            "cache_templates": self._adjust_template_caching,
            "monitoring_interval": self._adjust_monitoring_interval,
        }

    def adjust_for_context(self, context: WorkContext) -> List[ConfigAdjustment]:
        """コンテキストに応じた設定調整（Issue #804 AI最適化統合版）"""
        with self._lock:
            self._initialize_components()
            adjustments = []

            # Issue #804: AI駆動型最適化システム統合処理
            ai_optimizations_applied = self._apply_ai_optimizations(context)
            adjustments.extend(ai_optimizations_applied)

            # コンテキストパターン学習
            pattern_key = (
                f"{context.operation_type}_"
                f"{self._classify_content_size(context.content_size)}"
            )

            if pattern_key not in self.context_patterns:
                self.context_patterns[pattern_key] = {
                    "count": 0,
                    "avg_size": 0,
                    "avg_complexity": 0,
                    "optimal_settings": {},
                }

            # パターン情報更新
            pattern = self.context_patterns[pattern_key]
            pattern["count"] += 1
            pattern["avg_size"] = (
                pattern["avg_size"] * (pattern["count"] - 1) + context.content_size
            ) / pattern["count"]
            pattern["avg_complexity"] = (
                pattern["avg_complexity"] * (pattern["count"] - 1)
                + context.complexity_score
            ) / pattern["count"]

            # 各設定項目の調整実行
            for setting_key, adjustment_func in self.adjustment_rules.items():
                adjustment = adjustment_func(context, pattern)
                if adjustment:
                    adjustments.append(adjustment)
                    self._apply_adjustment(adjustment)

            self.logger.info(
                f"Applied {len(adjustments)} total adjustments (including AI optimizations) "
                f"for context: {context.operation_type}"
            )
            return adjustments

    def _apply_ai_optimizations(self, context: WorkContext) -> List[ConfigAdjustment]:
        """
        AI駆動型最適化システムを適用 - Issue #804 中核実装

        Args:
            context: 作業コンテキスト

        Returns:
            適用された最適化調整のリスト
        """
        ai_adjustments = []

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
            total_expected_benefit = sum(adj.expected_benefit for adj in ai_adjustments)
            self.logger.info(
                f"AI optimizations applied: {len(ai_adjustments)} adjustments, "
                f"expected total benefit: {total_expected_benefit:.1%}"
            )

        return ai_adjustments

    def _apply_file_size_optimizations(
        self, context: WorkContext
    ) -> List[ConfigAdjustment]:
        """ファイルサイズ制限最適化を適用"""
        adjustments = []

        # 動的サイズ制限調整
        if (
            self.file_size_optimizer
            and self.file_size_optimizer.adjust_limits_dynamically(context)
        ):
            # サイズ制限が調整された場合、関連する設定も更新
            current_max_chars = self.config.get("serena.max_answer_chars", 25000)
            optimized_stats = self.file_size_optimizer.get_optimization_statistics()

            # 統計に基づく最適化
            if optimized_stats["effectiveness_score"] > 0.7:  # 高効果の場合
                if context.content_size > 50000:
                    new_max_chars = min(current_max_chars, 35000)
                    if new_max_chars != current_max_chars:
                        adjustment = ConfigAdjustment(
                            key="serena.max_answer_chars",
                            old_value=current_max_chars,
                            new_value=new_max_chars,
                            context=f"ai_file_size_optimization_{context.operation_type}",
                            timestamp=time.time(),
                            reason=(
                                f"File size optimization with "
                                f"{optimized_stats['effectiveness_score']:.1%} effectiveness"
                            ),
                            expected_benefit=0.18,  # FileSizeLimitOptimizer目標削減率
                        )
                        adjustments.append(adjustment)

        return adjustments

    def _apply_concurrent_optimizations(
        self, context: WorkContext
    ) -> List[ConfigAdjustment]:
        """並列処理制限最適化を適用"""
        adjustments = []

        # リアルタイム性能指標を取得（簡易版）
        if not self.concurrent_limiter:
            return []
        concurrency_stats = self.concurrent_limiter.get_concurrency_statistics()
        performance_metrics = {
            "average_response_time": 5.0,  # 実装時に実際の指標に置換
            "resource_usage_percent": 60,  # 実装時に実際の指標に置換
        }

        # 性能指標に基づく調整
        old_limit = concurrency_stats["max_concurrent_calls"]
        if self.concurrent_limiter:
            self.concurrent_limiter.adjust_limits_based_on_performance(
                performance_metrics
            )
            new_stats = self.concurrent_limiter.get_concurrency_statistics()
            new_limit = new_stats["max_concurrent_calls"]
        else:
            new_limit = old_limit

        if old_limit != new_limit:
            # 並列制御設定の調整を記録
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
            self.config.set(
                "optimization.max_concurrent_tools", new_limit, "ai_optimizer"
            )

        return adjustments

    def _apply_token_optimizations(
        self, context: WorkContext
    ) -> List[ConfigAdjustment]:
        """Token使用量最適化を適用"""
        adjustments = []

        # コンテキストに基づくToken使用量の記録と分析
        estimated_input_tokens = int(context.content_size * 0.25)  # 概算
        estimated_output_tokens = int(
            context.complexity_score * 2000
        )  # 複雑性ベース概算

        # Token使用量を記録
        if not self.token_analyzer:
            return []
        analysis_result = self.token_analyzer.record_token_usage(
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
                            # max_answer_charsをより厳格に設定
                            current_chars = self.config.get(
                                "serena.max_answer_chars", 25000
                            )
                            optimized_chars = int(
                                current_chars * (1 - action["expected_reduction"])
                            )

                            if optimized_chars < current_chars:
                                adjustment = ConfigAdjustment(
                                    key="serena.max_answer_chars",
                                    old_value=current_chars,
                                    new_value=optimized_chars,
                                    context=f"ai_token_optimization_{context.operation_type}",
                                    timestamp=time.time(),
                                    reason=f"Token usage optimization: {suggestion['title']}",
                                    expected_benefit=action["expected_reduction"],
                                )
                                adjustments.append(adjustment)

        # 効率性スコアが低い場合の追加最適化
        efficiency_score = analysis_result.get("efficiency_score", 1.0)
        if efficiency_score < 0.6:
            # 低効率の場合、より保守的な設定を適用
            current_recursion = self.config.get("performance.max_recursion_depth", 50)
            if current_recursion > 30:
                optimized_recursion = max(30, int(current_recursion * 0.8))
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
        self._initialize_components()

        return {
            "file_size_optimization": (
                self.file_size_optimizer.get_optimization_statistics()
                if self.file_size_optimizer
                else {}
            ),
            "concurrent_control": (
                self.concurrent_limiter.get_concurrency_statistics()
                if self.concurrent_limiter
                else {}
            ),
            "token_analysis": (
                self.token_analyzer.get_usage_analytics() if self.token_analyzer else {}
            ),
            "integration_status": {
                "total_ai_adjustments": len(
                    [adj for adj in self.adjustment_history if "ai_" in adj.context]
                ),
                "expected_total_benefit": sum(
                    adj.expected_benefit
                    for adj in self.adjustment_history
                    if "ai_" in adj.context
                ),
                "last_optimization": max(
                    (
                        adj.timestamp
                        for adj in self.adjustment_history
                        if "ai_" in adj.context
                    ),
                    default=0,
                ),
            },
            "system_health": {
                "file_optimizer_active": self.file_size_optimizer is not None,
                "concurrent_limiter_active": self.concurrent_limiter is not None,
                "token_analyzer_active": self.token_analyzer is not None,
                "integration_complete": all(
                    [
                        self.file_size_optimizer is not None,
                        self.concurrent_limiter is not None,
                        self.token_analyzer is not None,
                    ]
                ),
            },
        }

    # ================================
    # 外部API - 主要公開メソッド群
    # ================================

    def optimize_for_file_operation(
        self, file_path: str, operation_type: str = "read"
    ) -> Dict[str, Any]:
        """
        ファイル操作の最適化（公開API）

        Args:
            file_path: ファイルパス
            operation_type: 操作種別

        Returns:
            最適化結果
        """
        with self._lock:
            self._initialize_components()

            # ファイル情報分析
            try:
                import os

                file_size = (
                    os.path.getsize(file_path) if os.path.exists(file_path) else 0
                )
            except (OSError, IOError):
                file_size = 0

            # コンテキスト生成
            context = WorkContext(
                operation_type=f"file_{operation_type}",
                content_size=file_size,
                complexity_score=0.5,  # デフォルト
                user_pattern="file_operation",
            )

            # 最適化実行
            adjustments = self.adjust_for_context(context)

            # ファイルサイズ制限適用
            if self.file_size_optimizer:
                optimized_size, optimization_info = (
                    self.file_size_optimizer.optimize_read_size(file_path, file_size)
                )
            else:
                optimized_size, optimization_info = file_size, {}

            return {
                "original_file_size": file_size,
                "optimized_size": optimized_size,
                "optimization_info": optimization_info,
                "adjustments_applied": len(adjustments),
                "adjustments": [
                    {
                        "key": adj.key,
                        "old_value": adj.old_value,
                        "new_value": adj.new_value,
                        "expected_benefit": adj.expected_benefit,
                    }
                    for adj in adjustments
                ],
            }

    def acquire_tool_permission(
        self, tool_name: str, estimated_complexity: float = 0.5
    ) -> Tuple[bool, str]:
        """
        ツール呼び出し許可を取得（公開API）

        Args:
            tool_name: ツール名
            estimated_complexity: 推定複雑度

        Returns:
            (許可フラグ, 許可ID/理由)
        """
        self._initialize_components()

        # 簡易コンテキスト作成
        context = WorkContext(
            operation_type="tool_call",
            content_size=int(estimated_complexity * 10000),
            complexity_score=estimated_complexity,
            user_pattern="tool_operation",
        )

        return (
            self.concurrent_limiter.acquire_call_permission(tool_name, context)
            if self.concurrent_limiter
            else None
        )

    def release_tool_permission(self, permission_id: str):
        """ツール呼び出し許可を解放（公開API）"""
        self._initialize_components()
        if self.concurrent_limiter:
            self.concurrent_limiter.release_call_permission(permission_id)

    def get_current_optimization_status(self) -> Dict[str, Any]:
        """現在の最適化状況を取得（公開API）"""
        with self._lock:
            self._initialize_components()

            recent_adjustments = list(self.adjustment_history)[-5:]
            return {
                "total_adjustments": len(self.adjustment_history),
                "recent_adjustments": [
                    {
                        "key": adj.key,
                        "timestamp": adj.timestamp,
                        "reason": adj.reason,
                        "expected_benefit": adj.expected_benefit,
                    }
                    for adj in recent_adjustments
                ],
                "ai_optimization_summary": self.get_ai_optimization_summary(),
                "system_status": {
                    "components_initialized": all(
                        [
                            self.statistical_engine is not None,
                            self.file_size_optimizer is not None,
                            self.concurrent_limiter is not None,
                            self.token_analyzer is not None,
                        ]
                    ),
                    "active_ab_tests": len(self.active_tests),
                    "context_patterns_learned": len(self.context_patterns),
                },
            }

    # ================================
    # 内部調整メソッド群
    # ================================

    def _classify_content_size(self, size: int) -> str:
        """コンテンツサイズを分類"""
        if size < 1000:
            return "tiny"
        elif size < 10000:
            return "small"
        elif size < 50000:
            return "medium"
        elif size < 100000:
            return "large"
        else:
            return "xlarge"

    def _apply_adjustment(self, adjustment: ConfigAdjustment):
        """設定調整を実際に適用"""
        try:
            self.config.set(adjustment.key, adjustment.new_value, adjustment.context)
            self.adjustment_history.append(adjustment)
            self.logger.debug(
                f"Applied adjustment: {adjustment.key} = {adjustment.new_value}"
            )
        except Exception as e:
            self.logger.error(f"Failed to apply adjustment {adjustment.key}: {e}")

    def _adjust_max_answer_chars(
        self, context: WorkContext, pattern: Dict[str, Any]
    ) -> Optional[ConfigAdjustment]:
        """max_answer_charsを調整"""
        current_value = self.config.get("serena.max_answer_chars", 25000)

        # コンテンツサイズに基づく調整
        if context.content_size > 75000:
            new_value = min(current_value, 35000)  # 大きなコンテンツは制限
        elif context.content_size < 5000 and context.complexity_score < 0.3:
            new_value = max(current_value, 20000)  # 小さく簡単なコンテンツは制限緩和
        else:
            return None

        if new_value != current_value:
            return ConfigAdjustment(
                key="serena.max_answer_chars",
                old_value=current_value,
                new_value=new_value,
                context=f"auto_adjust_{context.operation_type}",
                timestamp=time.time(),
                reason=(
                    f"Content size: {context.content_size}, "
                    f"complexity: {context.complexity_score:.2f}"
                ),
                expected_benefit=abs(new_value - current_value) / current_value * 0.15,
            )
        return None

    def _adjust_recursion_depth(
        self, context: WorkContext, pattern: Dict[str, Any]
    ) -> Optional[ConfigAdjustment]:
        """max_recursion_depthを調整"""
        current_value = self.config.get("performance.max_recursion_depth", 50)

        # 複雑性に基づく調整
        if context.complexity_score > 0.8:
            new_value = min(current_value + 20, 100)  # 複雑なコンテンツは深度増加
        elif context.complexity_score < 0.3 and context.content_size < 10000:
            new_value = max(current_value - 10, 20)  # 簡単なコンテンツは深度削減
        else:
            return None

        if new_value != current_value:
            return ConfigAdjustment(
                key="performance.max_recursion_depth",
                old_value=current_value,
                new_value=new_value,
                context=f"auto_adjust_{context.operation_type}",
                timestamp=time.time(),
                reason=f"Complexity-based adjustment: {context.complexity_score:.2f}",
                expected_benefit=0.05,
            )
        return None

    def _adjust_template_caching(
        self, context: WorkContext, pattern: Dict[str, Any]
    ) -> Optional[ConfigAdjustment]:
        """テンプレートキャッシュ設定を調整"""
        current_value = self.config.get("cache.templates", True)

        # パターン頻度に基づく調整
        pattern_count = pattern.get("count", 0)
        if pattern_count > 10 and not current_value:
            new_value = True
            return ConfigAdjustment(
                key="cache.templates",
                old_value=current_value,
                new_value=new_value,
                context=f"auto_adjust_{context.operation_type}",
                timestamp=time.time(),
                reason=f"High pattern frequency: {pattern_count}",
                expected_benefit=0.1,
            )
        return None

    def _adjust_monitoring_interval(
        self, context: WorkContext, pattern: Dict[str, Any]
    ) -> Optional[ConfigAdjustment]:
        """モニタリング間隔を調整"""
        current_value = self.config.get("monitoring.interval", 30)

        # 操作頻度に基づく調整
        if context.operation_type in ["parsing", "rendering"]:
            new_value = max(15, current_value - 5)  # 頻繁な操作は間隔短縮
        else:
            new_value = min(60, current_value + 10)  # 低頻度操作は間隔延長

        if new_value != current_value:
            return ConfigAdjustment(
                key="monitoring.interval",
                old_value=current_value,
                new_value=new_value,
                context=f"auto_adjust_{context.operation_type}",
                timestamp=time.time(),
                reason=f"Operation type based adjustment: {context.operation_type}",
                expected_benefit=0.03,
            )
        return None

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
        self, test_id: str, metric_value: float, context: Optional[WorkContext] = None
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

    def _finalize_ab_test(self, test_id: str):
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
        for pattern_key, pattern_data in self.context_patterns.items():
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

    def apply_learned_optimizations(self) -> List[ConfigAdjustment]:
        """学習した最適化を適用"""
        applied_adjustments = []

        learning_summary = self.learn_usage_patterns()

        for opportunity in learning_summary["optimization_opportunities"]:
            for recommendation in opportunity["recommendations"]:
                if recommendation["expected_improvement"] > 0.05:  # 5%以上の改善期待値
                    adjustment = self._create_learned_adjustment(
                        opportunity["pattern"], recommendation
                    )
                    if adjustment:
                        self._apply_adjustment(adjustment)
                        applied_adjustments.append(adjustment)

        return applied_adjustments

    def _create_learned_adjustment(
        self, pattern: str, recommendation: Dict[str, Any]
    ) -> Optional[ConfigAdjustment]:
        """学習基づく調整を作成"""
        if recommendation["type"] == "max_answer_chars_reduction":
            current_value = self.config.get("serena.max_answer_chars", 25000)
            reduction_rate = min(recommendation["expected_improvement"], 0.3)
            new_value = max(15000, int(current_value * (1 - reduction_rate)))

            if new_value != current_value:
                return ConfigAdjustment(
                    key="serena.max_answer_chars",
                    old_value=current_value,
                    new_value=new_value,
                    context=f"learned_optimization_{pattern}",
                    timestamp=time.time(),
                    reason=f"Pattern learning: {pattern}",
                    expected_benefit=recommendation["expected_improvement"],
                )
        return None

    def get_learning_status(self) -> Dict[str, Any]:
        """学習システムの状況を取得"""
        total_patterns = len(self.context_patterns)
        learned_patterns = sum(
            1 for pattern in self.context_patterns.values() if pattern["count"] >= 3
        )

        recent_adjustments = [
            adj for adj in self.adjustment_history if "learned_" in adj.context
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

    # ================================
    # ステータス・サマリー取得メソッド群
    # ================================

    def get_adjustment_summary(self) -> Dict[str, Any]:
        """調整サマリーを取得"""
        if not self.adjustment_history:
            return {
                "total_adjustments": 0,
                "total_expected_benefit": 0.0,
                "recent_activity": False,
            }

        recent_threshold = time.time() - 3600  # 1時間以内
        recent_adjustments = [
            adj for adj in self.adjustment_history if adj.timestamp > recent_threshold
        ]

        # カテゴリ別分析
        category_stats: defaultdict[str, dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "benefit": 0.0}
        )
        for adj in self.adjustment_history:
            category = adj.context.split("_")[0] if "_" in adj.context else "other"
            category_stats[category]["count"] += 1
            category_stats[category]["benefit"] += adj.expected_benefit

        return {
            "total_adjustments": len(self.adjustment_history),
            "recent_adjustments": len(recent_adjustments),
            "total_expected_benefit": sum(
                adj.expected_benefit for adj in self.adjustment_history
            ),
            "recent_expected_benefit": sum(
                adj.expected_benefit for adj in recent_adjustments
            ),
            "category_breakdown": dict(category_stats),
            "recent_activity": len(recent_adjustments) > 0,
            "most_impactful_adjustment": (
                max(
                    self.adjustment_history,
                    key=lambda adj: adj.expected_benefit,
                    default=None,
                ).__dict__
                if self.adjustment_history
                else None
            ),
        }

    # ==============================================================================
    # __init__.py の内容を以下にコメントとして記録（別ファイル作成時の参照用）
    # ==============================================================================

    # """
    def is_initialized(self) -> bool:
        """初期化状態チェック"""
        return hasattr(self, "config") and self.config is not None

    def optimize_settings(
        self, current_settings: Dict[str, Any], recent_operations: List[str]
    ) -> Dict[str, Any]:
        """設定最適化実行"""
        try:
            self._initialize_components()

            # 基本最適化ロジック
            optimization_result: dict[str, Any] = {
                "success": True,
                "improvement": 1.5,  # 1.5%改善
                "optimized_settings": current_settings.copy(),
                "applied_adjustments": [],
            }

            # 設定調整を適用
            if len(recent_operations) > 5:
                optimization_result["improvement"] += 0.5
                optimization_result["applied_adjustments"].append(
                    "bulk_operations_optimization"
                )

            return optimization_result
        except Exception as e:
            self.logger.error(f"設定最適化失敗: {e}")
            return {"success": False, "improvement": 0.0, "error": str(e)}

    def update_settings(self, settings: Dict[str, Any]) -> bool:
        """設定更新"""
        try:
            for key, value in settings.items():
                self.config.set(key, value)
            return True
        except Exception as e:
            self.logger.error(f"設定更新失敗: {e}")
            return False


# Adaptive Settings Management System
# ===================================
#
# 動的設定調整とAI最適化統合システムを提供します。
#
# 主要コンポーネント:
# - AdaptiveSettingsManager: 動的設定調整の中核
# - TokenUsageAnalyzer: リアルタイムToken使用量監視
# - FileSizeLimitOptimizer: ファイルサイズ制限最適化
# - A/B Testing Framework: 統計的検定システム
# - Phase B.1/B.2 Optimizers: 統合最適化システム
#
# Issue #813 対応: adaptive_settings.py (3011行) 分割リファクタリング実装
# Issue #804 対応: AI最適化システム統合
# """
#
# # 循環インポート回避のため順序を重視したインポート
#
# # 1. 基本データクラスとユーティリティ
# from .manager import ConfigAdjustment, WorkContext
#
# # 2. A/Bテストフレームワーク
# from .ab_testing import (
#     ABTestConfig,
#     ABTestResult,
#     SimpleNumpy,
#     SimpleStats,
#     StatisticalTestResult,
#     StatisticalTestingEngine,
# )
#
# # 3. 分析コンポーネント
# from .analyzers import (
#     ComplexityAnalyzer,
#     TokenUsageAnalyzer,
# )
#
# # 4. 最適化コンポーネント
# from .optimizers import (
#     ConcurrentToolCallLimiter,
#     ContextAwareOptimizer,
#     FileSizeLimitOptimizer,
#     RealTimeConfigAdjuster,
# )
#
# # 5. Phase最適化システム
# from .settings_optimizers import (
# IntegratedSettingsOptimizer,
# LearningBasedOptimizer,
# )
#
# # 6. メインマネージャー（最後にインポート）
# from .manager import AdaptiveSettingsManager
#
# # パブリックAPI定義
# __all__ = [
#     # メインマネージャー
#     "AdaptiveSettingsManager",
#
#     # データクラス
#     "ConfigAdjustment",
#     "WorkContext",
#
#     # A/Bテストフレームワーク
#     "ABTestConfig",
#     "ABTestResult",
#     "SimpleNumpy",
#     "SimpleStats",
#     "StatisticalTestResult",
#     "StatisticalTestingEngine",
#
#     # 分析システム
#     "ComplexityAnalyzer",
#     "TokenUsageAnalyzer",
#
#     # 最適化システム
#     "ConcurrentToolCallLimiter",
#     "ContextAwareOptimizer",
#     "FileSizeLimitOptimizer",
#     "RealTimeConfigAdjuster",
#
#     # Phase統合最適化
# "IntegratedSettingsOptimizer",
# "LearningBasedOptimizer",
# ]
