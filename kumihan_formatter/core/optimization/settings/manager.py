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
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

from kumihan_formatter.core.unified_config import EnhancedConfigAdapter as EnhancedConfig
from kumihan_formatter.core.utilities.logger import get_logger

if TYPE_CHECKING:
    from .ab_testing import ABTestConfig, ABTestResult, StatisticalTestingEngine
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
    monitoring_optimization_score: Optional[float] = None  # モニタリング最適化スコア (0.0-1.0)


class AdaptiveSettingsManager:
    """設定の動的最適化を管理するクラス"""

    def __init__(self):
        self.token_usage_tracker: Optional[Any] = None
        self.io_optimizer: Optional[Any] = None
        self.concurrency_limiter: Optional[Any] = None
        self.error_patterns: List[str] = []
        self.performance_history: List[Dict[str, Any]] = []
        self.optimization_stats: Dict[str, Any] = {}
        self.concurrency_stats: Dict[str, Any] = {}
        self.usage_analytics: Dict[str, Any] = {}
        self.context_detector: Optional[Any] = None
        self.realtime_adjuster: Optional[Any] = None

    def record_token_usage(self, usage_data: Dict[str, Any]) -> None:
        """トークン使用量を記録"""
        if self.token_usage_tracker:
            self.token_usage_tracker.record_token_usage(usage_data)

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """最適化統計を取得"""
        if self.token_usage_tracker:
            return self.token_usage_tracker.get_optimization_statistics()
        return {}

    def get_concurrency_statistics(self) -> Dict[str, Any]:
        """並行処理統計を取得"""
        if self.token_usage_tracker:
            return self.token_usage_tracker.get_concurrency_statistics()
        return {}

    def get_usage_analytics(self) -> Dict[str, Any]:
        """使用量分析を取得"""
        if self.token_usage_tracker:
            return self.token_usage_tracker.get_usage_analytics()
        return {}

    def optimize_read_size(self, base_size: int) -> int:
        """読み取りサイズを最適化"""
        if self.io_optimizer:
            return self.io_optimizer.optimize_read_size(base_size)
        return base_size

    def acquire_call_permission(self) -> bool:
        """API呼び出し許可を取得"""
        if self.concurrency_limiter:
            return self.concurrency_limiter.acquire_call_permission()
        return True

    def release_call_permission(self) -> None:
        """API呼び出し許可を解放"""
        if self.concurrency_limiter:
            self.concurrency_limiter.release_call_permission()

    def detect_context(self) -> Dict[str, Any]:
        """コンテキストを検出"""
        if self.context_detector:
            return self.context_detector.detect_context()
        return {}

    def start_realtime_adjustment(self) -> None:
        """リアルタイム調整を開始"""
        if self.realtime_adjuster:
            self.realtime_adjuster.start_realtime_adjustment()

    def stop_realtime_adjustment(self) -> None:
        """リアルタイム調整を停止"""
        if self.realtime_adjuster:
            self.realtime_adjuster.stop_realtime_adjustment()

    def get_adjustment_summary(self) -> Dict[str, Any]:
        """調整サマリーを取得"""
        if self.realtime_adjuster:
            return self.realtime_adjuster.get_adjustment_summary()
        return {}

    def adjust_for_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """コンテキストに応じた調整を実行"""
        if self.context_detector and self.realtime_adjuster:
            detected_context = self.context_detector.detect_context()
            merged_context = {**detected_context, **context}
            return self.realtime_adjuster.adjust_for_context(merged_context)
        return context

    @property
    def adjustment_history(self) -> List[Dict[str, Any]]:
        """調整履歴プロパティ"""
        if self.realtime_adjuster and hasattr(self.realtime_adjuster, "adjustment_history"):
            return self.realtime_adjuster.adjustment_history
        return []


# ==============================================================================
# __init__.py の内容を以下にコメントとして記録（別ファイル作成時の参照用）
# ==============================================================================

# """
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
