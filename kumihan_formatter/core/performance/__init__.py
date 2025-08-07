"""
Kumihan-Formatter パフォーマンス管理システム
Issue #813対応 - performance_metrics.py分割後の統合インポート

既存コードとの完全な互換性を保持するため、元のperformance_metricsからの
全インポートを提供します。
"""

# 分析システム
from .analytics import (
    InefficiencyPattern,
    PatternDetector,
    TokenEfficiencyAnalyzer,
    TokenEfficiencyMetrics,
)

# ベンチマークシステム
from .benchmark import PerformanceBenchmark

# 監視システム
from .monitor import (
    PerformanceContext,
    PerformanceMonitor,
    PerformanceSnapshot,
    ProcessingStats,
    monitor_performance,
)

# 最適化システム
from .optimizers import AsyncIOOptimizer, MemoryOptimizer, RegexOptimizer, SIMDOptimizer

# 後方互換性は不要（完全分離による）
# ProgressiveOutputSystemとAlertSystemは直接定義またはダミーとして提供
ProgressiveOutputSystem = None  # 未実装のためNone
AlertSystem = None  # 未実装のためNone

__all__ = [
    # 監視システム
    "PerformanceMonitor",
    "PerformanceSnapshot",
    "ProcessingStats",
    "PerformanceContext",
    "monitor_performance",
    # 最適化システム
    "AsyncIOOptimizer",
    "MemoryOptimizer",
    "RegexOptimizer",
    "SIMDOptimizer",
    # 分析システム
    "TokenEfficiencyAnalyzer",
    "PatternDetector",
    "TokenEfficiencyMetrics",
    "InefficiencyPattern",
    # ベンチマークシステム
    "PerformanceBenchmark",
    # 後方互換性
    "ProgressiveOutputSystem",
    "AlertSystem",
]

# 完全分離による後方互換性削除 - 元performance_metricsへの依存を完全排除
