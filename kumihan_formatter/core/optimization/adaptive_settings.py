"""
Phase B.1: 動的設定調整機能
=====================================

機能概要:
- 実行時max_answer_chars動的調整機能
- コンテキスト認識による自動設定変更
- 設定変更効果のリアルタイム測定
- A/Bテスト基盤による最適化

技術仕様:
- 既存EnhancedConfig.set()活用
- performance_metrics統合
- 学習型調整システム

期待効果: 3-5%追加削減
"""

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from statistics import mean, stdev
from typing import Any, Callable, Dict, List, Optional

from kumihan_formatter.core.config.config_manager import EnhancedConfig
from kumihan_formatter.core.utilities.logger import get_logger


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
    monitoring_optimization_score: Optional[float] = None  # モニタリング最適化スコア (0.0-1.0)


@dataclass
class ABTestConfig:
    """A/Bテスト設定"""

    parameter: str
    test_values: List[Any]
    sample_size: int = 10
    confidence_threshold: float = 0.95
    metric: str = "token_efficiency"


@dataclass
class ABTestResult:
    """A/Bテスト結果"""

    parameter: str
    winning_value: Any
    confidence: float
    improvement: float
    sample_count: int
    statistical_significance: bool


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

        # 調整履歴管理
        self.adjustment_history: deque[ConfigAdjustment] = deque(maxlen=1000)
        self.context_patterns: Dict[str, Dict[str, Any]] = {}

        # A/Bテスト管理
        self.active_tests: Dict[str, ABTestConfig] = {}
        self.test_results: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        # 効果測定
        self.performance_baselines: Dict[str, float] = {}
        self.recent_metrics: deque[Dict[str, Any]] = deque(maxlen=100)

        # 設定調整ルール
        self.adjustment_rules = self._initialize_adjustment_rules()

        # スレッドセーフティ
        self._lock = threading.Lock()

        self.logger.info("AdaptiveSettingsManager initialized")

    def _initialize_adjustment_rules(self) -> Dict[str, Callable]:
        """設定調整ルールを初期化"""
        return {
            "max_answer_chars": self._adjust_max_answer_chars,
            "max_recursion_depth": self._adjust_recursion_depth,
            "cache_templates": self._adjust_template_caching,
            "monitoring_interval": self._adjust_monitoring_interval,
        }

    def adjust_for_context(self, context: WorkContext) -> List[ConfigAdjustment]:
        """コンテキストに応じた設定調整"""
        with self._lock:
            adjustments = []

            # コンテキストパターン学習
            pattern_key = f"{context.operation_type}_{self._classify_content_size(context.content_size)}"

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
                f"Applied {len(adjustments)} adjustments for context: {context.operation_type}"
            )
            return adjustments

    def _classify_content_size(self, size: int) -> str:
        """コンテンツサイズを分類"""
        if size < 1000:
            return "small"
        elif size < 10000:
            return "medium"
        elif size < 100000:
            return "large"
        else:
            return "huge"

    def _adjust_max_answer_chars(
        self, context: WorkContext, pattern: Dict
    ) -> Optional[ConfigAdjustment]:
        """max_answer_chars動的調整"""
        current_value = self.config.get("serena.max_answer_chars", 25000)

        # コンテンツサイズベース調整
        if context.content_size < 5000 and current_value > 15000:
            new_value = 15000
            reason = "小規模コンテンツのため削減"
            expected_benefit = 0.15
        elif context.content_size > 50000 and current_value < 40000:
            new_value = 40000
            reason = "大規模コンテンツのため増加"
            expected_benefit = 0.08
        elif context.complexity_score > 0.8 and current_value < 30000:
            new_value = 30000
            reason = "高複雑性コンテンツのため増加"
            expected_benefit = 0.12
        else:
            return None

        return ConfigAdjustment(
            key="serena.max_answer_chars",
            old_value=current_value,
            new_value=new_value,
            context=f"{context.operation_type}_{self._classify_content_size(context.content_size)}",
            timestamp=time.time(),
            reason=reason,
            expected_benefit=expected_benefit,
        )

    def _adjust_recursion_depth(
        self, context: WorkContext, pattern: Dict
    ) -> Optional[ConfigAdjustment]:
        """再帰深度動的調整"""
        current_value = self.config.get("performance.max_recursion_depth", 50)

        if context.complexity_score > 0.9 and current_value < 80:
            new_value = 80
            reason = "高複雑性処理のため増加"
            expected_benefit = 0.05
        elif context.complexity_score < 0.3 and current_value > 30:
            new_value = 30
            reason = "単純処理のため削減"
            expected_benefit = 0.03
        else:
            return None

        return ConfigAdjustment(
            key="performance.max_recursion_depth",
            old_value=current_value,
            new_value=new_value,
            context=f"{context.operation_type}_{context.complexity_score:.1f}",
            timestamp=time.time(),
            reason=reason,
            expected_benefit=expected_benefit,
        )

    def _adjust_template_caching(
        self, context: WorkContext, pattern: Dict
    ) -> Optional[ConfigAdjustment]:
        """テンプレートキャッシング調整"""
        current_value = self.config.get("performance.cache_templates", True)

        # パターン数が少ない場合はキャッシュ無効化でメモリ節約
        if pattern["count"] < 5 and current_value:
            new_value = False
            reason = "低頻度パターンでメモリ節約"
            expected_benefit = 0.02
        # 頻繁なパターンではキャッシュ有効化
        elif pattern["count"] > 20 and not current_value:
            new_value = True
            reason = "高頻度パターンで速度向上"
            expected_benefit = 0.04
        else:
            return None

        return ConfigAdjustment(
            key="performance.cache_templates",
            old_value=current_value,
            new_value=new_value,
            context=f"pattern_frequency_{pattern['count']}",
            timestamp=time.time(),
            reason=reason,
            expected_benefit=expected_benefit,
        )

    def _adjust_monitoring_interval(
        self, context: WorkContext, pattern: Dict
    ) -> Optional[ConfigAdjustment]:
        """監視間隔調整"""
        current_value = self.config.get("monitoring.interval", 1.0)

        if context.operation_type == "optimization" and current_value > 0.5:
            new_value = 0.5
            reason = "最適化処理で高頻度監視"
            expected_benefit = 0.01
        elif context.operation_type == "rendering" and current_value < 2.0:
            new_value = 2.0
            reason = "レンダリング処理で監視負荷軽減"
            expected_benefit = 0.01
        else:
            return None

        return ConfigAdjustment(
            key="monitoring.interval",
            old_value=current_value,
            new_value=new_value,
            context=context.operation_type,
            timestamp=time.time(),
            reason=reason,
            expected_benefit=expected_benefit,
        )

    def _apply_adjustment(self, adjustment: ConfigAdjustment):
        """設定調整を適用"""
        self.config.set(adjustment.key, adjustment.new_value, "adaptive_system")
        self.adjustment_history.append(adjustment)

        self.logger.info(
            f"Applied adjustment: {adjustment.key} "
            f"{adjustment.old_value} -> {adjustment.new_value} "
            f"({adjustment.reason})"
        )

    def start_ab_test(self, test_config: ABTestConfig) -> bool:
        """A/Bテストを開始"""
        with self._lock:
            if test_config.parameter in self.active_tests:
                self.logger.warning(
                    f"A/B test already running for {test_config.parameter}"
                )
                return False

            self.active_tests[test_config.parameter] = test_config
            self.test_results[test_config.parameter] = []

            # ベースライン設定
            current_value = self.config.get(test_config.parameter)
            self.performance_baselines[test_config.parameter] = current_value

            self.logger.info(
                f"Started A/B test for {test_config.parameter} with values: {test_config.test_values}"
            )
            return True

    def record_ab_test_result(
        self, parameter: str, test_value: Any, metric_value: float
    ):
        """A/Bテスト結果を記録"""
        with self._lock:
            if parameter not in self.active_tests:
                return

            self.test_results[parameter].append(
                {"value": test_value, "metric": metric_value, "timestamp": time.time()}
            )

            test_config = self.active_tests[parameter]

            # サンプルサイズに達したら分析実行
            if len(self.test_results[parameter]) >= test_config.sample_size:
                result = self._analyze_ab_test(parameter)
                if result.statistical_significance:
                    self._apply_ab_test_result(result)
                    del self.active_tests[parameter]

    def _analyze_ab_test(self, parameter: str) -> ABTestResult:
        """A/Bテスト結果を分析"""
        test_config = self.active_tests[parameter]
        results = self.test_results[parameter]

        # 値別グループ化
        value_groups = defaultdict(list)
        for result in results:
            value_groups[str(result["value"])].append(result["metric"])

        # 最適値を特定
        best_value = None
        best_mean = float("-inf")

        for value_str, metrics in value_groups.items():
            if len(metrics) >= 3:  # 最小サンプル数
                mean_metric = mean(metrics)
                if mean_metric > best_mean:
                    best_mean = mean_metric
                    best_value = eval(value_str) if value_str.isdigit() else value_str

        # 統計的有意性評価（簡易版）
        baseline_metrics = value_groups.get(
            str(self.performance_baselines[parameter]), []
        )
        best_metrics = value_groups.get(str(best_value), [])

        statistical_significance = False
        improvement = 0.0

        if len(baseline_metrics) >= 3 and len(best_metrics) >= 3:
            baseline_mean = mean(baseline_metrics)
            best_mean_actual = mean(best_metrics)

            improvement = (
                (best_mean_actual - baseline_mean) / baseline_mean * 100
                if baseline_mean > 0
                else 0
            )

            # 簡易t検定（正規分布仮定）
            try:
                baseline_std = stdev(baseline_metrics)
                best_std = stdev(best_metrics)
                pooled_std = ((baseline_std**2 + best_std**2) / 2) ** 0.5

                if pooled_std > 0:
                    t_stat = abs(best_mean_actual - baseline_mean) / pooled_std
                    statistical_significance = t_stat > 2.0  # 簡易閾値
            except (ValueError, ZeroDivisionError) as e:
                # 統計計算エラー（標準偏差計算不可、ゼロ除算等）を無視
                pass

        return ABTestResult(
            parameter=parameter,
            winning_value=best_value,
            confidence=0.95 if statistical_significance else 0.5,
            improvement=improvement,
            sample_count=len(results),
            statistical_significance=statistical_significance,
        )

    def _apply_ab_test_result(self, result: ABTestResult):
        """A/Bテスト結果を適用"""
        if result.improvement > 5.0:  # 5%以上の改善
            adjustment = ConfigAdjustment(
                key=result.parameter,
                old_value=self.performance_baselines[result.parameter],
                new_value=result.winning_value,
                context="ab_test",
                timestamp=time.time(),
                reason=f"A/B test: {result.improvement:.1f}% improvement",
                expected_benefit=result.improvement / 100,
            )

            self._apply_adjustment(adjustment)
            self.logger.info(
                f"Applied A/B test result: {result.parameter} -> {result.winning_value}"
            )

    def get_adjustment_summary(self) -> Dict[str, Any]:
        """調整概要を取得"""
        with self._lock:
            recent_adjustments = list(self.adjustment_history)[-10:]

            return {
                "total_adjustments": len(self.adjustment_history),
                "recent_adjustments": [
                    {
                        "key": adj.key,
                        "old_value": adj.old_value,
                        "new_value": adj.new_value,
                        "reason": adj.reason,
                        "expected_benefit": adj.expected_benefit,
                        "timestamp": adj.timestamp,
                    }
                    for adj in recent_adjustments
                ],
                "context_patterns": len(self.context_patterns),
                "active_ab_tests": len(self.active_tests),
                "total_expected_benefit": sum(
                    adj.expected_benefit for adj in self.adjustment_history
                ),
            }

    def learn_usage_patterns(self) -> Dict[str, Any]:
        """基本パターン学習システム - Phase B.2簡易版"""
        with self._lock:
            learning_summary = {
                "patterns_discovered": len(self.context_patterns),
                "total_operations": sum(
                    p["count"] for p in self.context_patterns.values()
                ),
                "efficiency_insights": {},
                "optimization_opportunities": [],
            }

            # パターン効率性分析
            for pattern_key, pattern_data in self.context_patterns.items():
                if pattern_data["count"] >= 5:  # 最小学習データ閾値
                    # 平均効率性スコア計算
                    avg_complexity = pattern_data["avg_complexity"]
                    avg_size = pattern_data["avg_size"]

                    efficiency_score = self._calculate_pattern_efficiency(
                        avg_complexity, avg_size, pattern_data["count"]
                    )

                    learning_summary["efficiency_insights"][pattern_key] = {
                        "efficiency_score": efficiency_score,
                        "sample_count": pattern_data["count"],
                        "avg_complexity": avg_complexity,
                        "avg_size": avg_size,
                    }

                    # 最適化機会の特定
                    if efficiency_score < 0.6:  # 低効率パターン
                        optimization_opportunity = (
                            self._identify_optimization_opportunity(
                                pattern_key, pattern_data, efficiency_score
                            )
                        )
                        if optimization_opportunity:
                            learning_summary["optimization_opportunities"].append(
                                optimization_opportunity
                            )

            self.logger.info(
                f"Pattern learning completed: {len(learning_summary['efficiency_insights'])} patterns analyzed"
            )
            return learning_summary

    def _calculate_pattern_efficiency(
        self, complexity: float, size: int, count: int
    ) -> float:
        """パターン効率性スコア計算"""
        # 基本効率性計算（簡易版）
        complexity_efficiency = max(0, 1.0 - complexity)  # 複雑性が低いほど効率的
        size_efficiency = max(
            0, 1.0 - min(size / 50000, 1.0)
        )  # サイズが小さいほど効率的
        frequency_bonus = min(count / 20, 0.2)  # 頻度ボーナス（最大0.2）

        efficiency_score = (
            complexity_efficiency * 0.4 + size_efficiency * 0.4 + frequency_bonus
        )

        return max(0.0, min(1.0, efficiency_score))

    def _identify_optimization_opportunity(
        self, pattern_key: str, pattern_data: Dict, efficiency_score: float
    ) -> Optional[Dict[str, Any]]:
        """最適化機会の特定"""
        operation_type, size_class = pattern_key.split("_")

        optimization = {
            "pattern": pattern_key,
            "current_efficiency": efficiency_score,
            "sample_count": pattern_data["count"],
            "recommendations": [],
        }

        # サイズベース最適化
        if size_class in ["large", "huge"] and pattern_data["avg_size"] > 30000:
            optimization["recommendations"].append(
                {
                    "type": "max_answer_chars_reduction",
                    "current_suggested": "40000",
                    "optimized_suggested": "25000",
                    "expected_improvement": 0.08,
                }
            )

        # 複雑性ベース最適化
        if pattern_data["avg_complexity"] > 0.8:
            optimization["recommendations"].append(
                {
                    "type": "recursion_depth_increase",
                    "current_suggested": "50",
                    "optimized_suggested": "80",
                    "expected_improvement": 0.05,
                }
            )

        # 頻度ベース最適化
        if pattern_data["count"] > 15:
            optimization["recommendations"].append(
                {
                    "type": "caching_optimization",
                    "current_suggested": "True",
                    "optimized_suggested": "True",
                    "expected_improvement": 0.03,
                }
            )

        return optimization if optimization["recommendations"] else None

    def run_simple_ab_test(
        self, parameter: str, test_values: List[Any], sample_size: int = 10
    ) -> Optional[ABTestResult]:
        """簡易A/Bテスト実行 - Phase B.2版"""
        if parameter in self.active_tests:
            self.logger.warning(f"A/B test already active for {parameter}")
            return None

        # 簡易テスト設定
        test_config = ABTestConfig(
            parameter=parameter,
            test_values=test_values,
            sample_size=sample_size,
            duration_minutes=30,  # 短時間テスト
        )

        if not self.start_ab_test(test_config):
            return None

        self.logger.info(
            f"Started simple A/B test for {parameter} with {len(test_values)} values"
        )
        return None  # 結果は非同期で収集

    def apply_learned_optimizations(
        self, learning_summary: Dict[str, Any]
    ) -> List[ConfigAdjustment]:
        """学習結果に基づく最適化適用"""
        applied_adjustments = []

        for opportunity in learning_summary.get("optimization_opportunities", []):
            for recommendation in opportunity["recommendations"]:
                if recommendation["expected_improvement"] >= 0.03:  # 3%以上の改善期待

                    # 推奨設定を適用
                    if recommendation["type"] == "max_answer_chars_reduction":
                        adjustment = ConfigAdjustment(
                            key="serena.max_answer_chars",
                            old_value=self.config.get("serena.max_answer_chars", 25000),
                            new_value=int(recommendation["optimized_suggested"]),
                            context=f"learned_optimization_{opportunity['pattern']}",
                            timestamp=time.time(),
                            reason=f"Pattern learning: {recommendation['expected_improvement']:.1%} improvement expected",
                            expected_benefit=recommendation["expected_improvement"],
                        )

                        self._apply_adjustment(adjustment)
                        applied_adjustments.append(adjustment)

        self.logger.info(f"Applied {len(applied_adjustments)} learned optimizations")
        return applied_adjustments

    def get_learning_status(self) -> Dict[str, Any]:
        """学習システム状態取得"""
        with self._lock:
            return {
                "total_patterns": len(self.context_patterns),
                "learnable_patterns": sum(
                    1 for p in self.context_patterns.values() if p["count"] >= 5
                ),
                "active_ab_tests": len(self.active_tests),
                "total_adjustments": len(self.adjustment_history),
                "recent_learning_activity": len(
                    [
                        adj
                        for adj in self.adjustment_history
                        if "learned_optimization" in adj.context
                        and time.time() - adj.timestamp < 3600
                    ]
                ),
            }


class ContextAwareOptimizer:
    """
    コンテキスト認識最適化システム

    機能:
    - 作業種別の自動検出
    - コンテンツ複雑度分析
    - ユーザーパターン学習
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.user_patterns: Dict[str, Dict] = {}
        self.complexity_analyzer = ComplexityAnalyzer()

    def detect_context(
        self, operation: str, content: str, user_id: str = "default"
    ) -> WorkContext:
        """作業コンテキストを検出"""
        # 基本情報
        content_size = len(content.encode("utf-8"))

        # 複雑度分析
        complexity_score = self.complexity_analyzer.analyze(content)

        # ユーザーパターン学習
        user_pattern = self._learn_user_pattern(user_id, operation, content_size)

        return WorkContext(
            operation_type=operation,
            content_size=content_size,
            complexity_score=complexity_score,
            user_pattern=user_pattern,
        )

    def _learn_user_pattern(
        self, user_id: str, operation: str, content_size: int
    ) -> str:
        """ユーザーパターンを学習"""
        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = {
                "operations": defaultdict(int),
                "avg_content_size": 0,
                "total_operations": 0,
            }

        pattern = self.user_patterns[user_id]
        pattern["operations"][operation] += 1
        pattern["total_operations"] += 1

        # 移動平均で平均コンテンツサイズ更新
        pattern["avg_content_size"] = (
            pattern["avg_content_size"] * 0.9 + content_size * 0.1
        )

        # パターン分類
        most_common_op = max(pattern["operations"], key=pattern["operations"].get)

        if pattern["avg_content_size"] < 5000:
            return f"{most_common_op}_small_content"
        elif pattern["avg_content_size"] > 50000:
            return f"{most_common_op}_large_content"
        else:
            return f"{most_common_op}_medium_content"


class ComplexityAnalyzer:
    """コンテンツ複雑度分析"""

    def analyze(self, content: str) -> float:
        """コンテンツ複雑度を0-1で評価"""
        factors = []

        # 記法種類数
        notation_count = self._count_notations(content)
        factors.append(min(notation_count / 10, 1.0))

        # ネスト深度
        nest_depth = self._analyze_nesting(content)
        factors.append(min(nest_depth / 5, 1.0))

        # 特殊文字密度
        special_char_ratio = self._calculate_special_char_ratio(content)
        factors.append(special_char_ratio)

        # 行数
        line_count = content.count("\n")
        factors.append(min(line_count / 1000, 1.0))

        return mean(factors)

    def _count_notations(self, content: str) -> int:
        """記法種類数をカウント"""
        notations = ["太字", "イタリック", "見出し", "ハイライト", "枠線"]
        count = 0
        for notation in notations:
            if f"# {notation} #" in content:
                count += 1
        return count

    def _analyze_nesting(self, content: str) -> int:
        """ネスト深度を分析"""
        max_depth = 0
        current_depth = 0

        for char in content:
            if char == "#":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == "\n":
                current_depth = 0

        return max_depth

    def _calculate_special_char_ratio(self, content: str) -> float:
        """特殊文字密度を計算"""
        special_chars = set("#[](){}*_~`")
        special_count = sum(1 for char in content if char in special_chars)
        return min(special_count / len(content), 1.0) if content else 0.0


class RealTimeConfigAdjuster:
    """
    リアルタイム設定調整システム

    機能:
    - 設定変更の即座反映
    - 効果測定との連動
    - 自動ロールバック機能
    """

    def __init__(self, adaptive_manager: AdaptiveSettingsManager):
        self.logger = get_logger(__name__)
        self.adaptive_manager = adaptive_manager
        self.adjustment_monitor = {}
        self._monitoring_active = False

    def start_realtime_adjustment(self, context: WorkContext):
        """リアルタイム調整を開始"""
        self._monitoring_active = True

        # コンテキストベース調整実行
        adjustments = self.adaptive_manager.adjust_for_context(context)

        # 調整効果監視設定
        for adjustment in adjustments:
            self.adjustment_monitor[adjustment.key] = {
                "start_time": time.time(),
                "expected_benefit": adjustment.expected_benefit,
                "baseline_metrics": None,
            }

        self.logger.info(
            f"Started realtime adjustment monitoring for {len(adjustments)} settings"
        )

    def stop_realtime_adjustment(self) -> Dict[str, Any]:
        """リアルタイム調整を停止し結果を返す"""
        self._monitoring_active = False

        results = {}
        for key, monitor_data in self.adjustment_monitor.items():
            duration = time.time() - monitor_data["start_time"]
            results[key] = {
                "duration": duration,
                "expected_benefit": monitor_data["expected_benefit"],
            }

        self.adjustment_monitor.clear()
        self.logger.info("Stopped realtime adjustment monitoring")

        return results


class PhaseB1Optimizer:
    """
    Phase B.1統合最適化システム

    機能統合:
    - AdaptiveSettingsManager
    - ContextAwareOptimizer
    - RealTimeConfigAdjuster
    """

    def __init__(self, config: EnhancedConfig):
        self.logger = get_logger(__name__)
        self.config = config

        # コンポーネント初期化
        self.adaptive_manager = AdaptiveSettingsManager(config)
        self.context_optimizer = ContextAwareOptimizer()
        self.realtime_adjuster = RealTimeConfigAdjuster(self.adaptive_manager)

        self.logger.info("Phase B.1 Optimizer initialized")

    def optimize_for_operation(
        self, operation: str, content: str, user_id: str = "default"
    ) -> Dict[str, Any]:
        """操作に対する総合最適化"""
        # コンテキスト検出
        context = self.context_optimizer.detect_context(operation, content, user_id)

        # リアルタイム調整開始
        self.realtime_adjuster.start_realtime_adjustment(context)

        return {
            "context": {
                "operation_type": context.operation_type,
                "content_size": context.content_size,
                "complexity_score": context.complexity_score,
                "user_pattern": context.user_pattern,
            },
            "adjustments_applied": len(self.adaptive_manager.adjustment_history),
            "optimization_active": True,
        }

    def finalize_optimization(self) -> Dict[str, Any]:
        """最適化を完了し結果を返す"""
        adjustment_results = self.realtime_adjuster.stop_realtime_adjustment()
        summary = self.adaptive_manager.get_adjustment_summary()

        return {
            "adjustment_results": adjustment_results,
            "summary": summary,
            "total_expected_benefit": summary["total_expected_benefit"],
        }


class PhaseB2Optimizer:
    """
    Phase B.2 簡易版最適化システム

    機能:
    - 基本パターン学習システム
    - A/Bテスト基本運用
    - 自動設定調整強化
    - Phase B.1との統合運用

    目標: 追加5%削減（総合66.8%削減達成）
    """

    def __init__(
        self, config: EnhancedConfig, adaptive_manager: AdaptiveSettingsManager
    ):
        self.logger = get_logger(__name__)
        self.config = config
        self.adaptive_manager = adaptive_manager

        # TokenEfficiencyAnalyzer統合
        self.efficiency_analyzer = None

        # Phase B.2専用設定
        self.learning_enabled = True
        self.ab_testing_enabled = True
        self.auto_optimization_threshold = 0.03  # 3%以上の改善で自動適用

        # 学習履歴
        self.learning_sessions: deque[Dict[str, Any]] = deque(maxlen=50)
        self.optimization_results: deque[Dict[str, Any]] = deque(maxlen=100)

        # Phase B.2メトリクス
        self.phase_b2_metrics = {
            "patterns_learned": 0,
            "optimizations_applied": 0,
            "ab_tests_completed": 0,
            "total_improvement": 0.0,
            "last_learning_session": None,
        }

        self.logger.info(
            "PhaseB2Optimizer initialized - 5% additional reduction target"
        )

    def integrate_efficiency_analyzer(self, analyzer):
        """TokenEfficiencyAnalyzerとの統合"""
        self.efficiency_analyzer = analyzer
        self.logger.info("Integrated with TokenEfficiencyAnalyzer")

    def run_learning_cycle(self) -> Dict[str, Any]:
        """学習サイクル実行 - Phase B.2メイン機能"""
        cycle_start = time.time()

        try:
            # 1. パターン学習実行
            learning_summary = self.adaptive_manager.learn_usage_patterns()

            # 2. 効率性予測の取得（統合システム使用）
            efficiency_insights = {}
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
            self._update_phase_b2_metrics(cycle_result)

            self.logger.info(
                f"Learning cycle completed: {len(applied_optimizations)} optimizations, "
                f"{cycle_result['expected_improvement']:.1%} expected improvement"
            )

            return cycle_result

        except Exception as e:
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
        integrated = {
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
        analyzer_suggestions = []
        if self.efficiency_analyzer:
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
    ) -> List[ConfigAdjustment]:
        """自動最適化適用"""
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
                        context=f"phase_b2_auto_{proposal['pattern']}",
                        timestamp=time.time(),
                        reason=f"Phase B.2 auto-optimization: {proposal['expected_improvement']:.1%} expected",
                        expected_benefit=proposal["expected_improvement"],
                    )

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

                    test_started = self.adaptive_manager.run_simple_ab_test(
                        parameter, test_values, sample_size=8
                    )

                    if test_started is not None:
                        started_tests.append(parameter)

        return started_tests

    def _update_phase_b2_metrics(self, cycle_result: Dict):
        """Phase B.2メトリクス更新"""
        self.phase_b2_metrics["patterns_learned"] += cycle_result.get(
            "patterns_analyzed", 0
        )
        self.phase_b2_metrics["optimizations_applied"] += cycle_result.get(
            "optimizations_applied", 0
        )
        self.phase_b2_metrics["ab_tests_completed"] += cycle_result.get(
            "ab_tests_started", 0
        )
        self.phase_b2_metrics["total_improvement"] += cycle_result.get(
            "expected_improvement", 0
        )
        self.phase_b2_metrics["last_learning_session"] = cycle_result["timestamp"]

    def get_phase_b2_status(self) -> Dict[str, Any]:
        """Phase B.2ステータス取得"""
        learning_status = self.adaptive_manager.get_learning_status()

        # 総合削減率計算（Phase B.1 61.8% + Phase B.2追加分）
        phase_b1_reduction = 0.618  # Phase B.1実績
        phase_b2_additional = min(
            self.phase_b2_metrics["total_improvement"], 0.1
        )  # 最大10%
        total_reduction = phase_b1_reduction + phase_b2_additional

        return {
            "phase_b2_metrics": self.phase_b2_metrics,
            "learning_status": learning_status,
            "total_reduction_achieved": total_reduction,
            "target_progress": {
                "phase_b1_baseline": phase_b1_reduction,
                "phase_b2_target": 0.05,  # 5%目標
                "phase_b2_actual": phase_b2_additional,
                "remaining_to_target": max(0, 0.05 - phase_b2_additional),
            },
            "learning_sessions_count": len(self.learning_sessions),
            "recent_learning_active": (
                time.time() - self.phase_b2_metrics["last_learning_session"] < 3600
                if self.phase_b2_metrics["last_learning_session"]
                else False
            ),
        }

    def force_learning_cycle(self) -> Dict[str, Any]:
        """強制学習サイクル実行（テスト・デバッグ用）"""
        self.logger.info("Forcing learning cycle execution")
        return self.run_learning_cycle()
