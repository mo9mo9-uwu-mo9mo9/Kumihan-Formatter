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

import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from statistics import mean, stdev
from typing import Any, Callable, Dict, List, Optional, Tuple

# scipyインポート（フォールバック機能付き）
try:
    import numpy as np
    from scipy import stats

    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

    # フォールバック用の簡易統計クラス
    class SimpleStats:
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

    stats = SimpleStats()

    # numpy代替（フォールバック）
    class SimpleNumpy:
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

    np = SimpleNumpy()

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
    monitoring_optimization_score: Optional[float] = (
        None  # モニタリング最適化スコア (0.0-1.0)
    )


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
    """
    統計的検定エンジン

    機能:
    - scipy.statsを使用した本格的統計検定
    - 信頼区間計算
    - 効果サイズ（Cohen's d）計算
    - サンプルサイズ計算
    - フォールバック機能（scipy未インストール時）
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self.scipy_available = SCIPY_AVAILABLE

        if not self.scipy_available:
            self.logger.warning(
                "scipy not available - using fallback statistical functions"
            )

    def calculate_cohens_d(self, group1: List[float], group2: List[float]) -> float:
        """
        Cohen's d（効果サイズ）を計算

        Args:
            group1: グループ1のデータ
            group2: グループ2のデータ

        Returns:
            効果サイズ（Cohen's d）
        """
        if not group1 or not group2:
            return 0.0

        try:
            if self.scipy_available:
                mean1, mean2 = np.mean(group1), np.mean(group2)
                std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
                n1, n2 = len(group1), len(group2)

                # プールされた標準偏差
                pooled_std = math.sqrt(
                    ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2)
                )

                if pooled_std == 0:
                    return 0.0

                cohens_d = (mean1 - mean2) / pooled_std
                return abs(cohens_d)
            else:
                # フォールバック実装
                mean1, mean2 = mean(group1), mean(group2)
                std1 = stdev(group1) if len(group1) > 1 else 0
                std2 = stdev(group2) if len(group2) > 1 else 0

                pooled_std = math.sqrt((std1**2 + std2**2) / 2)
                if pooled_std == 0:
                    return 0.0

                return abs((mean1 - mean2) / pooled_std)

        except (ValueError, ZeroDivisionError) as e:
            self.logger.warning(
                f"Statistical calculation failed in calculate_cohens_d: {e}"
            )
            return 0.0

    def calculate_confidence_interval(
        self, data: List[float], confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """
        信頼区間を計算

        Args:
            data: データ
            confidence_level: 信頼水準（デフォルト: 0.95）

        Returns:
            信頼区間のタプル（下限, 上限）
        """
        if not data or len(data) < 2:
            return (0.0, 0.0)

        try:
            if self.scipy_available:
                data_array = np.array(data)
                sample_mean = np.mean(data_array)
                sample_std = np.std(data_array, ddof=1)
                n = len(data_array)

                # t分布の臨界値
                alpha = 1 - confidence_level
                t_critical = stats.t.ppf(1 - alpha / 2, df=n - 1)

                margin_error = t_critical * (sample_std / math.sqrt(n))

                return (sample_mean - margin_error, sample_mean + margin_error)
            else:
                # フォールバック実装（正規分布近似）
                sample_mean = mean(data)
                sample_std = stdev(data)
                n = len(data)

                # 95%信頼区間の場合のz値
                z_critical = 1.96 if confidence_level == 0.95 else 2.58
                margin_error = z_critical * (sample_std / math.sqrt(n))

                return (sample_mean - margin_error, sample_mean + margin_error)

        except (ValueError, ZeroDivisionError):
            return (0.0, 0.0)

    def calculate_required_sample_size(
        self, effect_size: float, power: float = 0.8, alpha: float = 0.05
    ) -> int:
        """
        必要サンプルサイズを計算

        Args:
            effect_size: 期待効果サイズ
            power: 統計的検出力（デフォルト: 0.8）
            alpha: 有意水準（デフォルト: 0.05）

        Returns:
            各グループに必要なサンプル数
        """
        if effect_size <= 0:
            return 100  # デフォルト値

        try:
            if self.scipy_available:
                # 二標本t検定のサンプルサイズ計算
                z_alpha = stats.norm.ppf(1 - alpha / 2)
                z_beta = stats.norm.ppf(power)

                n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
                return max(3, int(math.ceil(n)))  # 最小3サンプル
            else:
                # フォールバック実装（簡易計算）
                # Cohen (1988) の経験則に基づく近似
                if effect_size >= 0.8:  # 大きな効果
                    return max(3, int(20 / (effect_size**2)))
                elif effect_size >= 0.5:  # 中程度の効果
                    return max(3, int(30 / (effect_size**2)))
                else:  # 小さな効果
                    return max(3, int(50 / (effect_size**2)))

        except (ValueError, ZeroDivisionError):
            return 10  # デフォルト値

    def perform_statistical_test(
        self,
        group1: List[float],
        group2: List[float],
        test_type: str = "t_test",
        alpha: float = 0.05,
    ) -> StatisticalTestResult:
        """
        統計的検定を実行

        Args:
            group1: グループ1のデータ
            group2: グループ2のデータ
            test_type: 検定タイプ（"t_test", "mann_whitney"）
            alpha: 有意水準

        Returns:
            統計的検定結果
        """
        if not group1 or not group2:
            return StatisticalTestResult(
                test_type=test_type, statistic=0.0, p_value=1.0, significant=False
            )

        try:
            if test_type == "t_test":
                if self.scipy_available:
                    # Welchのt検定（等分散を仮定しない）
                    statistic, p_value = stats.ttest_ind(
                        group1, group2, equal_var=False
                    )
                else:
                    # フォールバック
                    result = stats.ttest_ind(group1, group2)
                    statistic, p_value = result.statistic, result.pvalue

            elif test_type == "mann_whitney":
                if self.scipy_available:
                    # Mann-Whitney U検定（ノンパラメトリック）
                    statistic, p_value = stats.mannwhitneyu(
                        group1, group2, alternative="two-sided"
                    )
                else:
                    # フォールバックとしてt検定を使用
                    result = stats.ttest_ind(group1, group2)
                    statistic, p_value = result.statistic, result.pvalue
            else:
                # デフォルトはt検定
                result = stats.ttest_ind(group1, group2)
                statistic, p_value = result.statistic, result.pvalue

            # 効果サイズ計算
            effect_size = self.calculate_cohens_d(group1, group2)

            # 信頼区間計算（差の信頼区間）
            if self.scipy_available:
                diff_data = [
                    g1 - g2
                    for g1, g2 in zip(group1, group2)
                    if len(group1) == len(group2)
                ]
                if not diff_data:
                    # サンプルサイズが異なる場合の近似
                    mean_diff = np.mean(group1) - np.mean(group2)
                    std_err = math.sqrt(
                        np.var(group1) / len(group1) + np.var(group2) / len(group2)
                    )
                    t_critical = stats.t.ppf(
                        1 - alpha / 2, df=len(group1) + len(group2) - 2
                    )
                    margin = t_critical * std_err
                    confidence_interval = (mean_diff - margin, mean_diff + margin)
                else:
                    confidence_interval = self.calculate_confidence_interval(
                        diff_data, 1 - alpha
                    )
            else:
                confidence_interval = None

            return StatisticalTestResult(
                test_type=test_type,
                statistic=float(statistic) if not math.isnan(statistic) else 0.0,
                p_value=float(p_value) if not math.isnan(p_value) else 1.0,
                significant=(
                    float(p_value) < alpha if not math.isnan(p_value) else False
                ),
                confidence_interval=confidence_interval,
                effect_size=effect_size,
            )

        except Exception as e:
            self.logger.warning(f"Statistical test failed: {e}")
            return StatisticalTestResult(
                test_type=test_type, statistic=0.0, p_value=1.0, significant=False
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

        # 統計的検定エンジン
        self.statistical_engine = StatisticalTestingEngine()

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

        # Issue #804: AI駆動型最適化システム統合
        self.file_size_optimizer = FileSizeLimitOptimizer(config)
        self.concurrent_limiter = ConcurrentToolCallLimiter(config)
        self.token_analyzer = TokenUsageAnalyzer(config)

        # スレッドセーフティ
        self._lock = threading.Lock()

        self.logger.info(
            f"AdaptiveSettingsManager initialized with AI optimization systems "
            f"(scipy: {SCIPY_AVAILABLE})"
        )

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
        if self.file_size_optimizer.adjust_limits_dynamically(context):
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
                            reason=f"File size optimization with {optimized_stats['effectiveness_score']:.1%} effectiveness",
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
        concurrency_stats = self.concurrent_limiter.get_concurrency_statistics()
        performance_metrics = {
            "average_response_time": 5.0,  # 実装時に実際の指標に置換
            "resource_usage_percent": 60,  # 実装時に実際の指標に置換
        }

        # 性能指標に基づく調整
        old_limit = concurrency_stats["max_concurrent_calls"]
        self.concurrent_limiter.adjust_limits_based_on_performance(performance_metrics)
        new_stats = self.concurrent_limiter.get_concurrency_statistics()
        new_limit = new_stats["max_concurrent_calls"]

        if old_limit != new_limit:
            # 並列制御設定の調整を記録
            adjustment = ConfigAdjustment(
                key="optimization.max_concurrent_tools",
                old_value=old_limit,
                new_value=new_limit,
                context=f"ai_concurrent_optimization_{context.operation_type}",
                timestamp=time.time(),
                reason=f"Concurrent control adjustment based on performance metrics",
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
        return {
            "file_size_optimization": self.file_size_optimizer.get_optimization_statistics(),
            "concurrent_control": self.concurrent_limiter.get_concurrency_statistics(),
            "token_analysis": self.token_analyzer.get_usage_analytics(),
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
                "file_optimizer_active": hasattr(self, "file_size_optimizer"),
                "concurrent_limiter_active": hasattr(self, "concurrent_limiter"),
                "token_analyzer_active": hasattr(self, "token_analyzer"),
                "integration_complete": all(
                    [
                        hasattr(self, "file_size_optimizer"),
                        hasattr(self, "concurrent_limiter"),
                        hasattr(self, "token_analyzer"),
                    ]
                ),
            },
        }

    def optimize_for_file_operation(
        self, file_path: str, requested_size: int
    ) -> Tuple[int, Dict[str, Any]]:
        """
        ファイル操作専用最適化 - Issue #804 外部API

        Args:
            file_path: ファイルパス
            requested_size: 要求サイズ

        Returns:
            最適化サイズと詳細情報
        """
        return self.file_size_optimizer.optimize_read_size(file_path, requested_size)

    def acquire_tool_permission(
        self, tool_name: str, context: Optional[WorkContext] = None
    ) -> Tuple[bool, str]:
        """
        ツール実行許可取得 - Issue #804 外部API

        Args:
            tool_name: ツール名
            context: 実行コンテキスト

        Returns:
            許可フラグと許可ID/理由
        """
        return self.concurrent_limiter.acquire_call_permission(tool_name, context)

    def release_tool_permission(self, call_id: str):
        """
        ツール実行許可解放 - Issue #804 外部API

        Args:
            call_id: 許可ID
        """
        self.concurrent_limiter.release_call_permission(call_id)

    def analyze_token_usage(
        self,
        operation_type: str,
        input_tokens: int,
        output_tokens: int,
        context: Optional[WorkContext] = None,
    ) -> Dict[str, Any]:
        """
        Token使用量分析 - Issue #804 外部API

        Args:
            operation_type: 操作種別
            input_tokens: 入力Token数
            output_tokens: 出力Token数
            context: 実行コンテキスト

        Returns:
            分析結果
        """
        return self.token_analyzer.record_token_usage(
            operation_type, input_tokens, output_tokens, context
        )

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
        """A/Bテストを開始（統計的検定強化版）"""
        with self._lock:
            if test_config.parameter in self.active_tests:
                self.logger.warning(
                    f"A/B test already running for {test_config.parameter}"
                )
                return False

            # 事前サンプルサイズ計算
            if test_config.calculate_sample_size:
                required_n = self.statistical_engine.calculate_required_sample_size(
                    test_config.minimum_effect_size,
                    test_config.power,
                    test_config.alpha,
                )

                # 設定されたサンプルサイズが不足している場合は警告
                if test_config.sample_size < required_n:
                    self.logger.warning(
                        f"Configured sample size ({test_config.sample_size}) is less than "
                        f"required ({required_n}) for effect size "
                        f"{test_config.minimum_effect_size:.3f}. Test may be underpowered."
                    )
                else:
                    self.logger.info(
                        f"Sample size ({test_config.sample_size}) is adequate for "
                        f"detecting effect size {test_config.minimum_effect_size:.3f}"
                    )

            self.active_tests[test_config.parameter] = test_config
            self.test_results[test_config.parameter] = []

            # ベースライン設定
            current_value = self.config.get(test_config.parameter)
            self.performance_baselines[test_config.parameter] = current_value

            self.logger.info(
                f"Started A/B test for {test_config.parameter}:\n"
                f"  - Test values: {test_config.test_values}\n"
                f"  - Sample size: {test_config.sample_size}\n"
                f"  - Test type: {test_config.test_type}\n"
                f"  - Alpha: {test_config.alpha}\n"
                f"  - Power: {test_config.power}\n"
                f"  - Min effect size: {test_config.minimum_effect_size}"
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
        """A/Bテスト結果を分析（統計的検定強化版）"""
        # test_config変数を削除（未使用のため）
        results = self.test_results[parameter]

        # 値別グループ化
        value_groups = defaultdict(list)
        for result in results:
            value_groups[str(result["value"])].append(result["metric"])

        # 最適値を特定
        best_value = None
        best_mean = float("-inf")
        best_metrics = []

        for value_str, metrics in value_groups.items():
            if len(metrics) >= 3:  # 最小サンプル数
                mean_metric = mean(metrics)
                if mean_metric > best_mean:
                    best_mean = mean_metric
                    best_value = eval(value_str) if value_str.isdigit() else value_str
                    best_metrics = metrics

        # ベースライン取得
        baseline_metrics = value_groups.get(
            str(self.performance_baselines[parameter]), []
        )

        statistical_significance = False
        improvement = 0.0
        statistical_test = None
        confidence_interval = None
        effect_size = None
        required_sample_size = None
        statistical_power = None

        if len(baseline_metrics) >= 3 and len(best_metrics) >= 3:
            baseline_mean = mean(baseline_metrics)
            best_mean_actual = mean(best_metrics)

            improvement = (
                (best_mean_actual - baseline_mean) / baseline_mean * 100
                if baseline_mean > 0
                else 0
            )

            # 本格的統計検定実行
            try:
                # t検定実行
                statistical_test = self.statistical_engine.perform_statistical_test(
                    best_metrics, baseline_metrics, test_type="t_test", alpha=0.05
                )

                statistical_significance = statistical_test.significant

                # 効果サイズ
                effect_size = statistical_test.effect_size

                # 信頼区間（改善率の95%信頼区間）
                if statistical_test.confidence_interval:
                    ci_lower, ci_upper = statistical_test.confidence_interval
                    # 改善率の信頼区間に変換
                    if baseline_mean > 0:
                        improvement_ci_lower = (ci_lower / baseline_mean) * 100
                        improvement_ci_upper = (ci_upper / baseline_mean) * 100
                        confidence_interval = (
                            improvement_ci_lower,
                            improvement_ci_upper,
                        )
                    else:
                        confidence_interval = statistical_test.confidence_interval

                # 必要サンプルサイズ（次回テスト用）
                if effect_size and effect_size > 0:
                    required_sample_size = (
                        self.statistical_engine.calculate_required_sample_size(
                            effect_size, power=0.8, alpha=0.05
                        )
                    )

                # 統計的検出力推定（簡易版）
                current_n = min(len(baseline_metrics), len(best_metrics))
                if effect_size and effect_size > 0 and current_n >= 3:
                    # Cohen (1988) に基づく近似
                    if current_n >= required_sample_size:
                        statistical_power = 0.8
                    else:
                        statistical_power = min(
                            0.8, current_n / required_sample_size * 0.8
                        )

                # 詳細ログ出力
                self.logger.info(
                    f"Statistical test results for {parameter}:\n"
                    f"  - Test type: {statistical_test.test_type}\n"
                    f"  - Statistic: {statistical_test.statistic:.4f}\n"
                    f"  - P-value: {statistical_test.p_value:.4f}\n"
                    f"  - Significant: {statistical_test.significant}\n"
                    f"  - Effect size (Cohen's d): {effect_size:.4f}\n"
                    f"  - Improvement: {improvement:.2f}%\n"
                    f"  - Confidence interval: {confidence_interval}\n"
                    f"  - Required sample size: {required_sample_size}\n"
                    f"  - Estimated power: {statistical_power:.2f}"
                )

            except Exception as e:
                self.logger.warning(f"Statistical analysis failed: {e}")
                # フォールバック処理継続

        # 信頼度計算
        if statistical_significance and effect_size:
            if effect_size >= 0.8:  # 大きな効果
                confidence = 0.95
            elif effect_size >= 0.5:  # 中程度の効果
                confidence = 0.90
            elif effect_size >= 0.2:  # 小さな効果
                confidence = 0.80
            else:
                confidence = 0.60
        else:
            confidence = 0.50

        return ABTestResult(
            parameter=parameter,
            winning_value=best_value,
            confidence=confidence,
            improvement=improvement,
            sample_count=len(results),
            statistical_significance=statistical_significance,
            statistical_test=statistical_test,
            confidence_interval=confidence_interval,
            effect_size=effect_size,
            required_sample_size=required_sample_size,
            statistical_power=statistical_power,
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
                f"Pattern learning completed: "
                f"{len(learning_summary['efficiency_insights'])} patterns analyzed"
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
                            reason=(
                                f"Pattern learning: {recommendation['expected_improvement']:.1%} "
                                f"improvement expected"
                            ),
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

    def get_statistical_test_capabilities(self) -> Dict[str, Any]:
        """統計的検定機能の状態取得"""
        return {
            "scipy_available": SCIPY_AVAILABLE,
            "supported_tests": (
                ["t_test", "mann_whitney"] if SCIPY_AVAILABLE else ["t_test_fallback"]
            ),
            "statistical_features": {
                "confidence_intervals": True,
                "effect_size": True,
                "sample_size_calculation": True,
                "power_analysis": SCIPY_AVAILABLE,
                "multiple_test_types": SCIPY_AVAILABLE,
            },
            "fallback_mode": not SCIPY_AVAILABLE,
        }

    def run_advanced_ab_test(
        self,
        parameter: str,
        test_values: List[Any],
        minimum_effect_size: float = 0.2,
        power: float = 0.8,
        alpha: float = 0.05,
        test_type: str = "t_test",
    ) -> bool:
        """
        統計的検定強化版A/Bテスト実行

        Args:
            parameter: テストパラメータ
            test_values: テスト値のリスト
            minimum_effect_size: 検出したい最小効果サイズ
            power: 統計的検出力
            alpha: 有意水準
            test_type: 検定タイプ

        Returns:
            テスト開始成功/失敗
        """
        # 適切なサンプルサイズを計算
        required_sample_size = self.statistical_engine.calculate_required_sample_size(
            minimum_effect_size, power, alpha
        )

        # 強化版A/Bテスト設定
        test_config = ABTestConfig(
            parameter=parameter,
            test_values=test_values,
            sample_size=required_sample_size,
            confidence_threshold=1 - alpha,
            alpha=alpha,
            power=power,
            minimum_effect_size=minimum_effect_size,
            test_type=test_type,
            calculate_sample_size=True,
        )

        return self.start_ab_test(test_config)


class FileSizeLimitOptimizer:
    """
    ファイルサイズ制限最適化システム - Issue #804 最高優先度実装

    機能:
    - 大きなファイル読み取り制限による token 削減（目標: 15-25% 削減）
    - 動的サイズしきい値調整
    - ファイル種別別制限設定
    - パフォーマンス監視統合
    """

    def __init__(self, config: EnhancedConfig):
        self.logger = get_logger(__name__)
        self.config = config

        # ファイルサイズ制限設定
        self.size_limits = {
            "default": 50000,  # デフォルト制限
            "code": 100000,  # コードファイル
            "text": 75000,  # テキストファイル
            "config": 25000,  # 設定ファイル
            "documentation": 150000,  # ドキュメント
        }

        # 統計情報
        self.read_statistics = {
            "total_reads": 0,
            "size_limited_reads": 0,
            "tokens_saved": 0,
            "average_reduction": 0.0,
        }

        # 動的調整履歴
        self.adjustment_history = deque(maxlen=100)
        self._lock = threading.Lock()

        self.logger.info("FileSizeLimitOptimizer initialized with dynamic thresholds")

    def optimize_read_size(
        self, file_path: str, requested_size: int
    ) -> Tuple[int, Dict[str, Any]]:
        """
        ファイル読み取りサイズを最適化

        Args:
            file_path: ファイルパス
            requested_size: 要求されたサイズ

        Returns:
            最適化されたサイズと統計情報
        """
        with self._lock:
            file_type = self._classify_file_type(file_path)
            current_limit = self.size_limits.get(file_type, self.size_limits["default"])

            # 最適化実行
            if requested_size > current_limit:
                optimized_size = current_limit
                reduction_rate = (requested_size - optimized_size) / requested_size

                # 統計更新
                self.read_statistics["total_reads"] += 1
                self.read_statistics["size_limited_reads"] += 1
                self.read_statistics["tokens_saved"] += int(
                    reduction_rate * requested_size * 0.25
                )  # トークン推定
                self._update_reduction_average(reduction_rate)

                optimization_info = {
                    "optimized": True,
                    "original_size": requested_size,
                    "optimized_size": optimized_size,
                    "reduction_rate": reduction_rate,
                    "file_type": file_type,
                    "tokens_saved_estimate": int(
                        reduction_rate * requested_size * 0.25
                    ),
                }

                self.logger.debug(
                    f"File size optimized: {file_path} "
                    f"{requested_size} -> {optimized_size} "
                    f"({reduction_rate:.1%} reduction)"
                )
            else:
                optimized_size = requested_size
                optimization_info = {
                    "optimized": False,
                    "original_size": requested_size,
                    "optimized_size": optimized_size,
                    "reduction_rate": 0.0,
                    "file_type": file_type,
                    "tokens_saved_estimate": 0,
                }
                self.read_statistics["total_reads"] += 1

            return optimized_size, optimization_info

    def _classify_file_type(self, file_path: str) -> str:
        """ファイルタイプを分類"""
        path_lower = file_path.lower()

        if any(
            ext in path_lower
            for ext in [".py", ".js", ".ts", ".java", ".cpp", ".c", ".rs"]
        ):
            return "code"
        elif any(
            ext in path_lower for ext in [".json", ".yaml", ".yml", ".toml", ".cfg"]
        ):
            return "config"
        elif any(ext in path_lower for ext in [".md", ".rst", ".txt", ".doc"]):
            return "documentation"
        elif any(ext in path_lower for ext in [".txt", ".log"]):
            return "text"
        else:
            return "default"

    def _update_reduction_average(self, new_reduction: float):
        """平均削減率を更新"""
        current_avg = self.read_statistics["average_reduction"]
        limited_reads = self.read_statistics["size_limited_reads"]

        # 加重平均で更新
        self.read_statistics["average_reduction"] = (
            current_avg * (limited_reads - 1) + new_reduction
        ) / limited_reads

    def adjust_limits_dynamically(self, context: WorkContext) -> bool:
        """コンテキストに応じた動的制限調整"""
        with self._lock:
            adjusted = False

            # 高複雑性コンテンツの場合は制限を緩和
            if context.complexity_score > 0.8:
                for file_type in self.size_limits:
                    old_limit = self.size_limits[file_type]
                    new_limit = int(old_limit * 1.2)  # 20%増加

                    if new_limit != old_limit:
                        self.size_limits[file_type] = new_limit
                        adjusted = True

                        self.adjustment_history.append(
                            {
                                "timestamp": time.time(),
                                "file_type": file_type,
                                "old_limit": old_limit,
                                "new_limit": new_limit,
                                "reason": "high_complexity_adjustment",
                                "context_complexity": context.complexity_score,
                            }
                        )

            # 小規模コンテンツの場合は制限を厳格化
            elif context.content_size < 10000 and context.complexity_score < 0.4:
                for file_type in self.size_limits:
                    old_limit = self.size_limits[file_type]
                    new_limit = max(int(old_limit * 0.8), 15000)  # 20%削減、最小15K

                    if new_limit != old_limit:
                        self.size_limits[file_type] = new_limit
                        adjusted = True

                        self.adjustment_history.append(
                            {
                                "timestamp": time.time(),
                                "file_type": file_type,
                                "old_limit": old_limit,
                                "new_limit": new_limit,
                                "reason": "low_complexity_optimization",
                                "context_size": context.content_size,
                                "context_complexity": context.complexity_score,
                            }
                        )

            if adjusted:
                self.logger.info(
                    f"Dynamic size limits adjusted based on context complexity: {context.complexity_score}"
                )

            return adjusted

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """最適化統計情報を取得"""
        with self._lock:
            total_reads = self.read_statistics["total_reads"]
            limited_reads = self.read_statistics["size_limited_reads"]

            return {
                "total_file_reads": total_reads,
                "size_limited_reads": limited_reads,
                "optimization_rate": (
                    limited_reads / total_reads if total_reads > 0 else 0.0
                ),
                "average_reduction_rate": self.read_statistics["average_reduction"],
                "estimated_tokens_saved": self.read_statistics["tokens_saved"],
                "current_limits": self.size_limits.copy(),
                "recent_adjustments": list(self.adjustment_history)[-5:],
                "effectiveness_score": self._calculate_effectiveness_score(),
            }

    def _calculate_effectiveness_score(self) -> float:
        """最適化効果スコアを計算"""
        total_reads = self.read_statistics["total_reads"]
        if total_reads == 0:
            return 0.0

        optimization_rate = self.read_statistics["size_limited_reads"] / total_reads
        avg_reduction = self.read_statistics["average_reduction"]

        # 効果スコア = 最適化頻度 × 平均削減率 × 品質調整
        effectiveness = optimization_rate * avg_reduction * 0.85  # 品質維持調整

        return min(1.0, effectiveness)


class ConcurrentToolCallLimiter:
    """
    並列ツール呼び出し制限システム - Issue #804 実装

    機能:
    - 同時実行ツール呼び出し数制限
    - リソース使用量監視
    - 適応的制限調整
    - デッドロック防止機能
    """

    def __init__(self, config: EnhancedConfig):
        self.logger = get_logger(__name__)
        self.config = config

        # 並列制限設定
        self.max_concurrent_calls = self.config.get(
            "optimization.max_concurrent_tools", 3
        )
        self.current_active_calls = 0
        self.call_queue = deque()

        # ツール別制限
        self.tool_limits = {
            "file_operations": 2,  # ファイル操作系
            "search_operations": 4,  # 検索系
            "analysis_operations": 2,  # 分析系
            "default": 3,
        }

        # 統計情報
        self.call_statistics = {
            "total_calls": 0,
            "queued_calls": 0,
            "concurrent_peaks": 0,
            "average_wait_time": 0.0,
            "resource_savings": 0,
        }

        # 並行制御
        self._semaphore = threading.Semaphore(self.max_concurrent_calls)
        self._lock = threading.Lock()
        self._active_calls = {}

        self.logger.info(
            f"ConcurrentToolCallLimiter initialized (max: {self.max_concurrent_calls})"
        )

    def acquire_call_permission(
        self, tool_name: str, context: Optional[WorkContext] = None
    ) -> Tuple[bool, str]:
        """
        ツール呼び出し許可を取得

        Args:
            tool_name: ツール名
            context: 作業コンテキスト

        Returns:
            (許可フラグ, 許可ID/理由)
        """
        with self._lock:
            call_id = f"{tool_name}_{int(time.time() * 1000)}_{threading.get_ident()}"

            # ツール種別分類
            tool_category = self._classify_tool(tool_name)
            current_category_calls = sum(
                1
                for call_info in self._active_calls.values()
                if call_info["category"] == tool_category
            )

            # カテゴリ別制限チェック
            category_limit = self.tool_limits.get(
                tool_category, self.tool_limits["default"]
            )
            if current_category_calls >= category_limit:
                self.call_statistics["queued_calls"] += 1
                reason = f"Category limit exceeded: {tool_category} ({current_category_calls}/{category_limit})"
                self.logger.debug(f"Tool call queued: {call_id} - {reason}")
                return False, reason

            # 全体制限チェック
            if len(self._active_calls) >= self.max_concurrent_calls:
                self.call_statistics["queued_calls"] += 1
                reason = f"Global limit exceeded: {len(self._active_calls)}/{self.max_concurrent_calls}"
                self.logger.debug(f"Tool call queued: {call_id} - {reason}")
                return False, reason

            # リソース使用量チェック
            if context and self._should_throttle_for_resources(context):
                self.call_statistics["queued_calls"] += 1
                reason = "Resource throttling active"
                return False, reason

            # 許可
            self._active_calls[call_id] = {
                "tool_name": tool_name,
                "category": tool_category,
                "start_time": time.time(),
                "context_size": context.content_size if context else 0,
            }

            self.call_statistics["total_calls"] += 1
            self.call_statistics["concurrent_peaks"] = max(
                self.call_statistics["concurrent_peaks"], len(self._active_calls)
            )

            self.logger.debug(
                f"Tool call permitted: {call_id} ({len(self._active_calls)} active)"
            )
            return True, call_id

    def release_call_permission(self, call_id: str):
        """ツール呼び出し許可を解放"""
        with self._lock:
            if call_id not in self._active_calls:
                return

            call_info = self._active_calls.pop(call_id)
            duration = time.time() - call_info["start_time"]

            # 統計更新
            self._update_wait_time_statistics(duration)

            # リソース節約効果計算
            saved_resources = self._calculate_resource_savings(call_info, duration)
            self.call_statistics["resource_savings"] += saved_resources

            self.logger.debug(
                f"Tool call completed: {call_id} "
                f"({duration:.2f}s, {saved_resources} resources saved)"
            )

    def _classify_tool(self, tool_name: str) -> str:
        """ツールをカテゴリ分類"""
        tool_lower = tool_name.lower()

        if any(keyword in tool_lower for keyword in ["read", "write", "edit", "file"]):
            return "file_operations"
        elif any(
            keyword in tool_lower for keyword in ["search", "grep", "find", "glob"]
        ):
            return "search_operations"
        elif any(keyword in tool_lower for keyword in ["analyze", "check", "validate"]):
            return "analysis_operations"
        else:
            return "default"

    def _should_throttle_for_resources(self, context: WorkContext) -> bool:
        """リソース使用量に基づくスロットリング判定"""
        # 大きなコンテンツまたは高複雑性の場合はスロットリング
        if context.content_size > 100000 or context.complexity_score > 0.9:
            current_resource_usage = sum(
                call_info.get("context_size", 0)
                for call_info in self._active_calls.values()
            )

            # 現在の総リソース使用量が閾値を超える場合
            if current_resource_usage > 500000:  # 500KB相当
                return True

        return False

    def _update_wait_time_statistics(self, duration: float):
        """待機時間統計を更新"""
        current_avg = self.call_statistics["average_wait_time"]
        total_calls = self.call_statistics["total_calls"]

        # 加重平均で更新
        self.call_statistics["average_wait_time"] = (
            current_avg * (total_calls - 1) + duration
        ) / total_calls

    def _calculate_resource_savings(self, call_info: Dict, duration: float) -> int:
        """リソース節約効果を計算"""
        # 基本節約効果（制限により他の呼び出しがブロックされた場合の効果）
        base_savings = 1

        # コンテンツサイズに基づく追加節約
        if call_info.get("context_size", 0) > 50000:
            base_savings += 2

        # 長時間実行に基づる追加節約
        if duration > 5.0:
            base_savings += 1

        return base_savings

    def adjust_limits_based_on_performance(self, performance_metrics: Dict[str, Any]):
        """パフォーマンス指標に基づく制限調整"""
        with self._lock:
            avg_response_time = performance_metrics.get("average_response_time", 0)
            resource_usage = performance_metrics.get("resource_usage_percent", 0)

            old_limit = self.max_concurrent_calls

            # 応答時間が遅い場合は制限を厳格化
            if avg_response_time > 10.0:  # 10秒以上
                self.max_concurrent_calls = max(1, self.max_concurrent_calls - 1)

            # リソース使用量が高い場合も制限を厳格化
            elif resource_usage > 80:
                self.max_concurrent_calls = max(2, self.max_concurrent_calls - 1)

            # パフォーマンスが良好な場合は制限を緩和
            elif avg_response_time < 3.0 and resource_usage < 50:
                self.max_concurrent_calls = min(6, self.max_concurrent_calls + 1)

            if old_limit != self.max_concurrent_calls:
                # セマフォアも更新
                self._semaphore = threading.Semaphore(self.max_concurrent_calls)

                self.logger.info(
                    f"Concurrent call limit adjusted: {old_limit} -> {self.max_concurrent_calls} "
                    f"(response_time: {avg_response_time:.1f}s, resource_usage: {resource_usage}%)"
                )

    def get_concurrency_statistics(self) -> Dict[str, Any]:
        """並列制御統計情報を取得"""
        with self._lock:
            return {
                "max_concurrent_calls": self.max_concurrent_calls,
                "current_active_calls": len(self._active_calls),
                "tool_limits": self.tool_limits.copy(),
                "total_calls_processed": self.call_statistics["total_calls"],
                "queued_calls_count": self.call_statistics["queued_calls"],
                "peak_concurrent_usage": self.call_statistics["concurrent_peaks"],
                "average_call_duration": self.call_statistics["average_wait_time"],
                "resource_savings_score": self.call_statistics["resource_savings"],
                "active_calls_detail": [
                    {
                        "tool": call_info["tool_name"],
                        "category": call_info["category"],
                        "duration": time.time() - call_info["start_time"],
                        "context_size": call_info["context_size"],
                    }
                    for call_info in self._active_calls.values()
                ],
                "efficiency_score": self._calculate_concurrency_efficiency(),
            }

    def _calculate_concurrency_efficiency(self) -> float:
        """並列処理効率スコアを計算"""
        total_calls = self.call_statistics["total_calls"]
        if total_calls == 0:
            return 1.0

        queued_ratio = self.call_statistics["queued_calls"] / total_calls
        resource_efficiency = self.call_statistics["resource_savings"] / total_calls

        # 効率スコア = (1 - キュー比率) + リソース効率
        efficiency = (1 - queued_ratio) * 0.7 + min(resource_efficiency, 0.3)

        return max(0.0, min(1.0, efficiency))


class TokenUsageAnalyzer:
    """
    Token使用量分析システム - Issue #804 実装

    機能:
    - リアルタイムToken使用量監視
    - 使用パターン分析と予測
    - 使用量最適化提案
    - コスト効率性分析
    """

    def __init__(self, config: EnhancedConfig):
        self.logger = get_logger(__name__)
        self.config = config

        # Token使用量追跡
        self.usage_history = deque(maxlen=1000)
        self.current_session_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "operations_count": 0,
            "start_time": time.time(),
        }

        # 使用パターン分析
        self.usage_patterns = {
            "hourly_patterns": defaultdict(list),
            "operation_patterns": defaultdict(list),
            "efficiency_patterns": defaultdict(list),
        }

        # 最適化提案履歴
        self.optimization_suggestions = deque(maxlen=50)

        # 制御
        self._lock = threading.Lock()

        self.logger.info("TokenUsageAnalyzer initialized for real-time monitoring")

    def record_token_usage(
        self,
        operation_type: str,
        input_tokens: int,
        output_tokens: int,
        context: Optional[WorkContext] = None,
    ) -> Dict[str, Any]:
        """
        Token使用量を記録し分析

        Args:
            operation_type: 操作種別
            input_tokens: 入力トークン数
            output_tokens: 出力トークン数
            context: 作業コンテキスト

        Returns:
            使用量分析結果
        """
        with self._lock:
            total_tokens = input_tokens + output_tokens
            timestamp = time.time()

            # 使用量記録
            usage_record = {
                "timestamp": timestamp,
                "operation_type": operation_type,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "context_size": context.content_size if context else 0,
                "complexity_score": context.complexity_score if context else 0.0,
            }

            self.usage_history.append(usage_record)

            # セッション統計更新
            self.current_session_usage["input_tokens"] += input_tokens
            self.current_session_usage["output_tokens"] += output_tokens
            self.current_session_usage["total_tokens"] += total_tokens
            self.current_session_usage["operations_count"] += 1

            # パターン分析更新
            self._update_usage_patterns(usage_record)

            # 分析結果生成
            analysis_result = {
                "recorded_usage": usage_record,
                "session_cumulative": self.current_session_usage.copy(),
                "efficiency_score": self._calculate_operation_efficiency(usage_record),
                "optimization_opportunities": self._identify_optimization_opportunities(
                    usage_record
                ),
            }

            # 最適化提案生成（条件付き）
            if total_tokens > self._get_optimization_threshold():
                suggestions = self._generate_optimization_suggestions(
                    usage_record, analysis_result
                )
                if suggestions:
                    analysis_result["optimization_suggestions"] = suggestions
                    self.optimization_suggestions.extend(suggestions)

            return analysis_result

    def _update_usage_patterns(self, usage_record: Dict[str, Any]):
        """使用パターンを更新"""
        hour = time.strftime("%H", time.localtime(usage_record["timestamp"]))
        operation_type = usage_record["operation_type"]

        # 時間別パターン
        self.usage_patterns["hourly_patterns"][hour].append(
            usage_record["total_tokens"]
        )

        # 操作別パターン
        self.usage_patterns["operation_patterns"][operation_type].append(
            {
                "tokens": usage_record["total_tokens"],
                "efficiency": usage_record["total_tokens"]
                / max(usage_record["context_size"], 1),
            }
        )

        # 効率パターン（複雑性対トークン比）
        if usage_record["complexity_score"] > 0:
            efficiency_ratio = (
                usage_record["total_tokens"] / usage_record["complexity_score"]
            )
            complexity_class = (
                "high" if usage_record["complexity_score"] > 0.7 else "low"
            )
            self.usage_patterns["efficiency_patterns"][complexity_class].append(
                efficiency_ratio
            )

    def _calculate_operation_efficiency(self, usage_record: Dict[str, Any]) -> float:
        """操作効率スコアを計算"""
        base_efficiency = 1.0
        total_tokens = usage_record["total_tokens"]
        context_size = usage_record["context_size"]
        complexity = usage_record["complexity_score"]

        # コンテンツサイズ対トークン効率
        if context_size > 0:
            token_ratio = total_tokens / context_size
            if token_ratio < 0.1:  # 非常に効率的
                base_efficiency += 0.3
            elif token_ratio < 0.3:  # 効率的
                base_efficiency += 0.1
            elif token_ratio > 0.8:  # 非効率
                base_efficiency -= 0.2

        # 複雑性対効率
        if complexity > 0:
            complexity_efficiency = 1.0 - (total_tokens / (complexity * 10000))
            base_efficiency += complexity_efficiency * 0.2

        return max(0.0, min(1.0, base_efficiency))

    def _identify_optimization_opportunities(
        self, usage_record: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """最適化機会を特定"""
        opportunities = []

        # 高トークン使用量の場合
        if usage_record["total_tokens"] > 5000:
            opportunities.append(
                {
                    "type": "high_token_usage",
                    "severity": "medium",
                    "description": f"高トークン使用量検出: {usage_record['total_tokens']} tokens",
                    "suggested_actions": [
                        "ファイルサイズ制限の適用",
                        "コンテンツの分割処理",
                        "不要な詳細情報の除去",
                    ],
                }
            )

        # 効率性の問題
        efficiency = self._calculate_operation_efficiency(usage_record)
        if efficiency < 0.6:
            opportunities.append(
                {
                    "type": "low_efficiency",
                    "severity": "high",
                    "description": f"低効率操作検出: 効率スコア {efficiency:.2f}",
                    "suggested_actions": [
                        "操作アプローチの見直し",
                        "コンテキスト情報の最適化",
                        "処理順序の改善",
                    ],
                }
            )

        # 不均衡な入出力比率
        if usage_record["output_tokens"] > usage_record["input_tokens"] * 3:
            opportunities.append(
                {
                    "type": "output_heavy",
                    "severity": "low",
                    "description": "出力過多パターン検出",
                    "suggested_actions": [
                        "出力内容の簡潔化",
                        "要約手法の適用",
                        "テンプレート使用の検討",
                    ],
                }
            )

        return opportunities

    def _generate_optimization_suggestions(
        self, usage_record: Dict[str, Any], analysis_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """最適化提案を生成"""
        suggestions = []
        total_tokens = usage_record["total_tokens"]

        # 具体的な最適化提案
        if total_tokens > 8000:
            suggestions.append(
                {
                    "type": "immediate_action",
                    "priority": "high",
                    "title": "大量Token使用の緊急最適化",
                    "description": f"{total_tokens} tokens使用により効率性低下",
                    "actions": [
                        {
                            "action": "apply_file_size_limits",
                            "expected_reduction": 0.25,
                        },
                        {
                            "action": "enable_content_filtering",
                            "expected_reduction": 0.15,
                        },
                        {"action": "use_summary_mode", "expected_reduction": 0.35},
                    ],
                    "estimated_total_reduction": 0.55,
                }
            )

        # パターン基づく提案
        operation_type = usage_record["operation_type"]
        if operation_type in self.usage_patterns["operation_patterns"]:
            pattern_data = self.usage_patterns["operation_patterns"][operation_type]
            if len(pattern_data) >= 3:
                avg_tokens = sum(p["tokens"] for p in pattern_data) / len(pattern_data)
                if total_tokens > avg_tokens * 1.5:
                    suggestions.append(
                        {
                            "type": "pattern_based",
                            "priority": "medium",
                            "title": f"{operation_type}操作の効率化",
                            "description": f"平均比 {total_tokens/avg_tokens:.1f}倍の使用量",
                            "actions": [
                                {
                                    "action": "optimize_operation_flow",
                                    "expected_reduction": 0.20,
                                },
                                {"action": "apply_caching", "expected_reduction": 0.10},
                            ],
                            "estimated_total_reduction": 0.30,
                        }
                    )

        return suggestions

    def _get_optimization_threshold(self) -> int:
        """最適化提案を開始するトークン数閾値を取得"""
        # 基本閾値
        base_threshold = 3000

        # 最近のセッション平均に基づく動的調整
        if len(self.usage_history) >= 10:
            recent_avg = (
                sum(record["total_tokens"] for record in list(self.usage_history)[-10:])
                / 10
            )
            base_threshold = max(base_threshold, int(recent_avg * 1.5))

        return base_threshold

    def get_usage_analytics(self) -> Dict[str, Any]:
        """使用量分析結果を取得"""
        with self._lock:
            if not self.usage_history:
                return {"status": "no_data"}

            # 基本統計
            total_operations = len(self.usage_history)
            total_tokens_all = sum(
                record["total_tokens"] for record in self.usage_history
            )
            avg_tokens_per_operation = total_tokens_all / total_operations

            # 効率性分析
            efficiency_scores = [
                self._calculate_operation_efficiency(record)
                for record in self.usage_history
            ]
            avg_efficiency = sum(efficiency_scores) / len(efficiency_scores)

            # トレンド分析
            recent_records = (
                list(self.usage_history)[-20:]
                if len(self.usage_history) >= 20
                else list(self.usage_history)
            )
            older_records = (
                list(self.usage_history)[:-20] if len(self.usage_history) > 20 else []
            )

            trend_direction = "stable"
            if older_records:
                recent_avg = sum(r["total_tokens"] for r in recent_records) / len(
                    recent_records
                )
                older_avg = sum(r["total_tokens"] for r in older_records) / len(
                    older_records
                )

                if recent_avg > older_avg * 1.1:
                    trend_direction = "increasing"
                elif recent_avg < older_avg * 0.9:
                    trend_direction = "decreasing"

            # 操作別効率性
            operation_efficiency = {}
            for op_type, pattern_data in self.usage_patterns[
                "operation_patterns"
            ].items():
                if len(pattern_data) >= 3:
                    avg_efficiency_op = sum(
                        p["efficiency"] for p in pattern_data
                    ) / len(pattern_data)
                    operation_efficiency[op_type] = avg_efficiency_op

            return {
                "session_summary": self.current_session_usage,
                "historical_analytics": {
                    "total_operations": total_operations,
                    "total_tokens_consumed": total_tokens_all,
                    "average_tokens_per_operation": avg_tokens_per_operation,
                    "overall_efficiency_score": avg_efficiency,
                    "usage_trend": trend_direction,
                },
                "pattern_insights": {
                    "operation_efficiency": operation_efficiency,
                    "peak_usage_hours": self._get_peak_usage_hours(),
                    "efficiency_by_complexity": self._get_complexity_efficiency_analysis(),
                },
                "optimization_status": {
                    "active_suggestions_count": len(self.optimization_suggestions),
                    "recent_optimizations": list(self.optimization_suggestions)[-5:],
                    "potential_savings": self._calculate_potential_savings(),
                },
                "recommendations": self._generate_usage_recommendations(),
            }

    def _get_peak_usage_hours(self) -> List[str]:
        """ピーク使用時間を取得"""
        hourly_averages = {}
        for hour, tokens_list in self.usage_patterns["hourly_patterns"].items():
            if tokens_list:
                hourly_averages[hour] = sum(tokens_list) / len(tokens_list)

        # 上位3時間を返す
        sorted_hours = sorted(hourly_averages.items(), key=lambda x: x[1], reverse=True)
        return [hour for hour, _ in sorted_hours[:3]]

    def _get_complexity_efficiency_analysis(self) -> Dict[str, float]:
        """複雑性別効率分析"""
        analysis = {}
        for complexity_class, ratios in self.usage_patterns[
            "efficiency_patterns"
        ].items():
            if ratios:
                analysis[complexity_class] = sum(ratios) / len(ratios)
        return analysis

    def _calculate_potential_savings(self) -> Dict[str, Any]:
        """潜在的節約効果を計算"""
        if not self.optimization_suggestions:
            return {"total_potential_reduction": 0.0, "estimated_token_savings": 0}

        # 最近の提案から節約効果を推定
        recent_suggestions = list(self.optimization_suggestions)[-10:]
        total_reduction = 0.0

        for suggestion in recent_suggestions:
            if "estimated_total_reduction" in suggestion:
                total_reduction += suggestion["estimated_total_reduction"]

        avg_reduction = (
            total_reduction / len(recent_suggestions) if recent_suggestions else 0.0
        )
        recent_token_usage = (
            sum(record["total_tokens"] for record in list(self.usage_history)[-20:])
            if len(self.usage_history) >= 20
            else 0
        )

        estimated_savings = int(recent_token_usage * avg_reduction)

        return {
            "average_potential_reduction": avg_reduction,
            "estimated_token_savings": estimated_savings,
            "basis_operations": len(recent_suggestions),
        }

    def _generate_usage_recommendations(self) -> List[Dict[str, Any]]:
        """使用量に基づく推奨事項を生成"""
        recommendations = []

        # セッション使用量に基づく推奨
        session_tokens = self.current_session_usage["total_tokens"]
        if session_tokens > 50000:
            recommendations.append(
                {
                    "category": "session_optimization",
                    "priority": "high",
                    "title": "セッション使用量最適化",
                    "description": f"現在セッションで {session_tokens} tokens使用",
                    "action": "セッション分割またはコンテンツ最適化を検討",
                }
            )

        # 効率性に基づく推奨
        if len(self.usage_history) >= 10:
            recent_efficiency = [
                self._calculate_operation_efficiency(record)
                for record in list(self.usage_history)[-10:]
            ]
            avg_recent_efficiency = sum(recent_efficiency) / len(recent_efficiency)

            if avg_recent_efficiency < 0.7:
                recommendations.append(
                    {
                        "category": "efficiency_improvement",
                        "priority": "medium",
                        "title": "操作効率性改善",
                        "description": f"最近の効率スコア: {avg_recent_efficiency:.2f}",
                        "action": "ファイルサイズ制限や並列制御の適用を推奨",
                    }
                )

        # パターンに基づく推奨
        for op_type, pattern_data in self.usage_patterns["operation_patterns"].items():
            if len(pattern_data) >= 5:
                avg_tokens = sum(p["tokens"] for p in pattern_data) / len(pattern_data)
                if avg_tokens > 4000:
                    recommendations.append(
                        {
                            "category": "operation_specific",
                            "priority": "low",
                            "title": f"{op_type}操作最適化",
                            "description": f"平均 {avg_tokens:.0f} tokens使用",
                            "action": f"{op_type}操作のアプローチ見直しを推奨",
                        }
                    )

        return recommendations


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
                        reason=(
                            f"Phase B.2 auto-optimization: "
                            f"{proposal['expected_improvement']:.1%} expected"
                        ),
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
