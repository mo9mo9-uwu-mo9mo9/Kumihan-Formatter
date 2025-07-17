"""Performance logging and optimization for Kumihan-Formatter - 統合モジュール（後方互換性）

このモジュールはパフォーマンス追跡、監視、最適化機能を提供します。
Issue #492 Phase 5A - 分割により300行制限対応

注意: このモジュールは後方互換性のため保持。
新しい実装は分割されたモジュールを使用:
- performance_decorators: デコレーター関数
- performance_trackers: トラッキング機能
- performance_optimizer: 最適化クラス
- performance_factory: ファクトリー関数
"""

from typing import Any, Callable, Optional, Union

# 分割されたモジュールからインポート
from .performance_decorators import log_performance_decorator
from .performance_factory import get_log_performance_optimizer
from .performance_optimizer import LogPerformanceOptimizer
from .performance_trackers import call_chain_tracker, memory_usage_tracker

# 後方互換性のため、全ての関数・クラスを再エクスポート
__all__ = [
    "log_performance_decorator",
    "call_chain_tracker",
    "memory_usage_tracker",
    "LogPerformanceOptimizer",
    "get_log_performance_optimizer",
]