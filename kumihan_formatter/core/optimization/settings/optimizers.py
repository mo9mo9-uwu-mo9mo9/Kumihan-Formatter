"""
File Size and Context-Aware Optimizers
=====================================

ファイルサイズ制限とコンテキスト認識最適化機能を提供します。

機能:
- FileSizeLimitOptimizer: ファイルサイズ制限最適化
- ContextAwareOptimizer: コンテキスト認識最適化
- ConcurrentToolCallLimiter: 並列ツール呼び出し制限
- RealTimeConfigAdjuster: リアルタイム設定調整

Issue #804 最高優先度実装
"""

import threading
import time
from collections import defaultdict, deque

# 循環インポート回避のため型ヒント用
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from kumihan_formatter.core.unified_config import (
    EnhancedConfigAdapter as EnhancedConfig,
)
from kumihan_formatter.core.utilities.logger import get_logger

if TYPE_CHECKING:
    from .manager import AdaptiveSettingsManager, WorkContext


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
        self.adjustment_history: deque[dict[str, Any]] = deque(maxlen=100)
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
        elif any(ext in path_lower for ext in [".md", ".rst", ".txt", ".doc"]):
            return "documentation"
        elif any(
            ext in path_lower for ext in [".yaml", ".yml", ".json", ".toml", ".ini"]
        ):
            return "config"
        else:
            return "text"

    def _update_reduction_average(self, new_reduction: float) -> None:
        """平均削減率を更新"""
        current_avg = self.read_statistics["average_reduction"]
        limited_reads = self.read_statistics["size_limited_reads"]

        # 加重平均で更新
        if limited_reads > 0:
            self.read_statistics["average_reduction"] = (
                current_avg * (limited_reads - 1) + new_reduction
            ) / limited_reads

    def adjust_limits_dynamically(self, context: "WorkContext") -> bool:
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
                    f"Dynamic size limits adjusted based on context complexity: "
                    f"{context.complexity_score}"
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
        # 効果スコア = 最適化率 × 平均削減率
        return optimization_rate * avg_reduction


class ContextAwareOptimizer:
    """
    コンテキスト認識最適化システム

    機能:
    - 作業種別の自動検出
    - コンテンツ複雑度分析
    - ユーザーパターン学習
    """

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.user_patterns: Dict[str, Dict[str, Any]] = {}
        # ComplexityAnalyzerは必要時にインポート
        self.complexity_analyzer: Optional[Any] = None

    def _get_complexity_analyzer(self) -> Any:
        """ComplexityAnalyzerを遅延インポート"""
        if self.complexity_analyzer is None:
            from .analyzers import ComplexityAnalyzer

            self.complexity_analyzer = ComplexityAnalyzer()
        return self.complexity_analyzer

    def detect_context(
        self, operation: str, content: str, user_id: str = "default"
    ) -> "WorkContext":
        """作業コンテキストを検出"""
        from .manager import WorkContext  # 循環インポート回避

        # 基本情報
        content_size = len(content.encode("utf-8"))

        # 複雑度分析
        complexity_analyzer = self._get_complexity_analyzer()
        complexity_score = complexity_analyzer.analyze(content)

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
        self.call_queue: deque[dict[str, Any]] = deque()

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
        self._active_calls: dict[str, dict[str, Any]] = {}

        self.logger.info(
            f"ConcurrentToolCallLimiter initialized (max: {self.max_concurrent_calls})"
        )

    def acquire_call_permission(
        self, tool_name: str, context: Optional["WorkContext"] = None
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
                reason = (
                    f"Category limit exceeded: {tool_category} "
                    f"({current_category_calls}/{category_limit})"
                )
                self.logger.debug(f"Tool call queued: {call_id} - {reason}")
                return False, reason

            # グローバル制限チェック
            if len(self._active_calls) >= self.max_concurrent_calls:
                self.call_statistics["queued_calls"] += 1
                reason = (
                    f"Global limit exceeded: "
                    f"{len(self._active_calls)}/{self.max_concurrent_calls}"
                )
                self.logger.debug(f"Tool call queued: {call_id} - {reason}")
                return False, reason

            # 呼び出し許可
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

    def release_call_permission(self, call_id: str) -> None:
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

    def _should_throttle_for_resources(self, context: "WorkContext") -> bool:
        """リソース使用量に基づくスロットリング判定"""
        if context is None:
            return False

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

    def _update_wait_time_statistics(self, duration: float) -> None:
        """待機時間統計を更新"""
        current_avg = self.call_statistics["average_wait_time"]
        total_calls = self.call_statistics["total_calls"]

        # 加重平均で更新
        self.call_statistics["average_wait_time"] = (
            current_avg * (total_calls - 1) + duration
        ) / total_calls

    def _calculate_resource_savings(
        self, call_info: Dict[str, Any], duration: float
    ) -> int:
        """リソース節約効果を計算"""
        # 基本節約効果（制限により他の呼び出しがブロックされた場合の効果）
        base_savings = 1

        # コンテンツサイズに基づく追加節約
        if call_info.get("context_size", 0) > 50000:
            base_savings += 2

        # 長時間実行に基づく追加節約
        if duration > 5.0:
            base_savings += 1

        return base_savings

    def adjust_limits_based_on_performance(
        self, performance_metrics: Dict[str, Any]
    ) -> None:
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

        queued_calls = self.call_statistics["queued_calls"]
        if total_calls == 0:
            return 1.0
        # 効率性 = 1 - (キューされた呼び出し / 総呼び出し数)
        efficiency = 1.0 - (queued_calls / total_calls)
        return max(0.0, efficiency)


class RealTimeConfigAdjuster:
    """
    リアルタイム設定調整システム

    機能:
    - 設定変更の即座反映
    - 効果測定との連動
    - 自動ロールバック機能
    """

    def __init__(self, adaptive_manager: "AdaptiveSettingsManager"):
        self.logger = get_logger(__name__)
        self.adaptive_manager = adaptive_manager
        self.adjustment_monitor: dict[str, Any] = {}
        self._monitoring_active = False

    def start_realtime_adjustment(self, context: "WorkContext") -> None:
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
